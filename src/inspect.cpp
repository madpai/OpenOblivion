// SPDX-License-Identifier: GPL-3.0-only
// Original OpenOblivion orchestration around the unchanged OpenMW reader.
#include <components/esm4/common.hpp>
#include <components/esm4/reader.hpp>
#include <components/toutf8/toutf8.hpp>

#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>

namespace
{
    constexpr std::uint64_t maxFileBytes = 2ULL * 1024 * 1024 * 1024;
    constexpr std::uint32_t maxRecordBytes = 32U * 1024 * 1024;
    constexpr std::uint64_t maxRecords = 2'000'000;
    constexpr unsigned maxDepth = 64;

    std::uint32_t read32(std::istream& file)
    {
        std::array<unsigned char, 4> bytes{};
        if (!file.read(reinterpret_cast<char*>(bytes.data()), bytes.size()))
            throw std::runtime_error("Truncated integer");
        return std::uint32_t(bytes[0]) | (std::uint32_t(bytes[1]) << 8)
            | (std::uint32_t(bytes[2]) << 16) | (std::uint32_t(bytes[3]) << 24);
    }

    struct Envelope
    {
        std::uint64_t records = 0;
        std::uint64_t groups = 0;
        std::uint64_t compressed = 0;
        std::map<std::string, std::uint64_t> types;
    };

    // This checks container bounds and budgets; it does not interpret TES4 records.
    void validateRange(std::ifstream& file, std::uint64_t start, std::uint64_t end,
        unsigned depth, Envelope& result)
    {
        if (depth > maxDepth)
            throw std::runtime_error("Group nesting budget exceeded");
        for (auto at = start; at < end;)
        {
            if (end - at < 20)
                throw std::runtime_error("Truncated classic TES4 header");
            file.seekg(static_cast<std::streamoff>(at));
            std::array<char, 4> tag{};
            file.read(tag.data(), tag.size());
            for (char c : tag)
                if (!((c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_'))
                    throw std::runtime_error("Invalid record signature");
            const std::string type(tag.data(), tag.size());
            const auto size = read32(file);
            const auto flags = read32(file);
            if (type == "GRUP")
            {
                if (size < 20 || size > end - at)
                    throw std::runtime_error("Group exceeds parent bounds");
                if (++result.groups > maxRecords)
                    throw std::runtime_error("Group count budget exceeded");
                validateRange(file, at + 20, at + size, depth + 1, result);
                at += size;
            }
            else
            {
                if (size > maxRecordBytes || size > end - at - 20)
                    throw std::runtime_error("Record exceeds bounds or budget");
                if (++result.records > maxRecords)
                    throw std::runtime_error("Record count budget exceeded");
                ++result.types[type];
                if (flags & 0x00040000U)
                {
                    if (size < 4)
                        throw std::runtime_error("Truncated compressed record");
                    file.seekg(static_cast<std::streamoff>(at + 20));
                    if (read32(file) > maxRecordBytes)
                        throw std::runtime_error("Decompressed record exceeds budget");
                    ++result.compressed;
                }
                at += 20 + size;
            }
        }
    }

    Envelope validate(const std::filesystem::path& path)
    {
        const auto bytes = std::filesystem::file_size(path);
        if (bytes < 38 || bytes > maxFileBytes)
            throw std::runtime_error("File exceeds size bounds");
        std::ifstream file(path, std::ios::binary);
        if (!file)
            throw std::runtime_error("Cannot open input");
        std::array<char, 4> signature{};
        file.read(signature.data(), signature.size());
        if (std::string(signature.data(), 4) != "TES4")
            throw std::runtime_error("Expected a classic TES4 plugin");
        file.seekg(20);
        file.read(signature.data(), signature.size());
        std::array<unsigned char, 2> hedrSize{};
        file.read(reinterpret_cast<char*>(hedrSize.data()), hedrSize.size());
        if (std::string(signature.data(), 4) != "HEDR" || hedrSize[0] != 12 || hedrSize[1] != 0)
            throw std::runtime_error("Expected classic HEDR; later game formats are unsupported");
        const auto version = read32(file);
        if (version != 0x3f800000U && version != 0x3f99999aU)
            throw std::runtime_error("Unsupported classic plugin version");
        Envelope result;
        validateRange(file, 0, bytes, 0, result);
        return result;
    }
}

int main(int argc, char** argv)
{
    if (argc == 2 && std::string(argv[1]) == "--help")
    {
        std::cout << "Usage: openoblivion-inspect PLUGIN\nRead-only classic TES4 structure/subrecord scan.\n"
                     "Reports counts only. It does not load a playable world.\n";
        return 0;
    }
    if (argc != 2)
    {
        std::cerr << "Usage: openoblivion-inspect PLUGIN\n";
        return 2;
    }
    try
    {
        const std::filesystem::path path(argv[1]);
        const auto envelope = validate(path);
        const ToUTF8::StatelessUtf8Encoder encoder(ToUTF8::calculateEncoding("win1252"));
        auto stream = std::make_unique<std::ifstream>(path, std::ios::binary);
        ESM4::Reader reader(std::move(stream), path, nullptr, &encoder, true);
        std::uint64_t records = 1; // TES4 header is consumed by the constructor.
        std::uint64_t groups = 0;
        std::uint64_t subrecords = 0;
        // Inspect a header before testing the next-item cursor. The upstream
        // readAll helper tests that cursor after reading the header and can
        // omit the last record. Container parsing itself remains upstream.
        while (reader.hasMoreRecs())
        {
            reader.exitGroupCheck();
            if (!reader.getRecordHeader())
                throw std::runtime_error("Upstream reader could not read a validated header");
            if (reader.hdr().record.typeId == ESM4::REC_GRUP)
            {
                ++groups;
                reader.enterGroup();
                continue;
            }
            ++records;
            reader.getRecordData(false);
            while (reader.getSubRecordHeader())
            {
                ++subrecords;
                reader.skipSubRecordData();
            }
        }
        if (records != envelope.records || groups != envelope.groups)
            throw std::runtime_error("Upstream traversal differs from validated envelope: records "
                + std::to_string(records) + "/" + std::to_string(envelope.records) + ", groups "
                + std::to_string(groups) + "/" + std::to_string(envelope.groups));
        std::cout << "{\"schema\":1,\"classic_tes4\":true,\"file_bytes\":" << reader.getFileSize()
                  << ",\"header_version\":" << reader.esmVersionF()
                  << ",\"records_including_header\":" << records
                  << ",\"groups\":" << groups << ",\"compressed_records\":" << envelope.compressed
                  << ",\"scanned_subrecords_excluding_header\":" << subrecords << ",\"record_types\":{";
        bool first = true;
        for (const auto& [type, count] : envelope.types)
        {
            if (!first)
                std::cout << ',';
            first = false;
            std::cout << '"' << type << "\":" << count;
        }
        std::cout << "}}\n";
        return 0;
    }
    catch (const std::exception& error)
    {
        std::cerr << "Inspection failed: " << error.what() << '\n';
        return 1;
    }
}
