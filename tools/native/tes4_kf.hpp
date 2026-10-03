// SPDX-License-Identifier: GPL-3.0-only
// Original TES4 KF adapter using audited OpenMW APIs. No game data included.
#pragma once
#include "openoblivion_tes4_animation.hpp"
#include <components/nif/controller.hpp>
#include <components/nif/data.hpp>
#include <components/nif/extra.hpp>
#include <components/nifosg/controller.hpp>
#include <components/nifosg/matrixtransform.hpp>
#include <components/sceneutil/keyframe.hpp>
#include <components/misc/strings/algorithm.hpp>
#include <components/debug/debuglog.hpp>
#include <memory>
#include <stdexcept>
#include <unordered_map>
#include <vector>

namespace OpenOblivion::Animation
{
    using Pose = SceneUtil::KeyframeController::KfTransform;

    inline Pose defaults(const Nif::NiQuatTransform& transform)
    {
        Pose pose;
        const auto& p = transform.mTranslation;
        const auto& q = transform.mRotation;
        if (validValue(p.x()) && validValue(p.y()) && validValue(p.z())) pose.mTranslation = p;
        if (validValue(q.x()) && validValue(q.y()) && validValue(q.z()) && validValue(q.w())
            && q.length2() > 0) pose.mRotation = q;
        if (validValue(transform.mScale)) pose.mScale = transform.mScale;
        return pose;
    }

    class TransformTrack : public NifOsg::KeyframeController
    {
    public:
        TransformTrack() = default;
        TransformTrack(const Nif::NiKeyframeController* key, const Nif::NiTransformInterpolator& interp)
            : NifOsg::KeyframeController(key), mDefaults(defaults(interp.mDefaultValue))
        {
            mHasTranslation = !interp.mData.empty() && interp.mData->mTranslations
                && !interp.mData->mTranslations->mKeys.empty();
        }
        TransformTrack(const TransformTrack& copy, const osg::CopyOp& op)
            : osg::Object(copy, op), NifOsg::KeyframeController(copy, op),
              mDefaults(copy.mDefaults), mHasTranslation(copy.mHasTranslation) {}
        META_Object(OpenOblivion, TransformTrack)
        Pose getCurrentTransformation(osg::NodeVisitor* nv) override
        {
            auto out = NifOsg::KeyframeController::getCurrentTransformation(nv);
            if (hasInput())
            {
                if (!out.mTranslation) out.mTranslation = mDefaults.mTranslation;
                if (!out.mRotation) out.mRotation = mDefaults.mRotation;
                if (!out.mScale) out.mScale = mDefaults.mScale;
            }
            return out;
        }
        osg::Vec3f getTranslation(float time) const override
        {
            return mHasTranslation ? NifOsg::KeyframeController::getTranslation(time)
                : mDefaults.mTranslation.value_or(osg::Vec3f{});
        }
    private:
        Pose mDefaults;
        bool mHasTranslation{false};
    };

    struct SplineStorage
    {
        std::vector<float> floats;
        std::vector<std::int16_t> shorts;
    };

    class SplineTrack : public SceneUtil::KeyframeController,
                        public SceneUtil::NodeCallback<SplineTrack, NifOsg::MatrixTransform*>
    {
    public:
        SplineTrack() = default;
        SplineTrack(const Nif::NiBSplineTransformInterpolator& interp, std::shared_ptr<const SplineStorage> data)
            : mData(std::move(data)), mDefaults(defaults(interp.mValue)),
              mStart(interp.mStartTime), mStop(interp.mStopTime)
        {
            mHandles = {interp.mTranslationHandle, interp.mRotationHandle, interp.mScaleHandle};
            if (!interp.mBasisData.empty()) mCount = interp.mBasisData->mNumControlPoints;
            if (auto* compact = dynamic_cast<const Nif::NiBSplineCompTransformInterpolator*>(&interp))
            {
                mCompact = true;
                mOffsets = {compact->mTranslationOffset, compact->mRotationOffset, compact->mScaleOffset};
                mRanges = {compact->mTranslationHalfRange, compact->mRotationHalfRange, compact->mScaleHalfRange};
            }
            if (!std::isfinite(mStart) || !std::isfinite(mStop) || mStop < mStart)
                throw std::runtime_error("Invalid spline time bounds");
            // Validate every declared channel now, while loading the clip.
            // A missing handle is a static/default channel; a truncated channel
            // must not silently become a plausible but incorrect static pose.
            if (!missingHandle(mHandles[0]) && !channel<3>(0, 0.f)) throw std::runtime_error("Invalid spline translation channel");
            if (!missingHandle(mHandles[1]) && !channel<4>(1, 0.f)) throw std::runtime_error("Invalid spline rotation channel");
            if (!missingHandle(mHandles[2]) && !channel<1>(2, 0.f)) throw std::runtime_error("Invalid spline scale channel");
        }
        SplineTrack(const SplineTrack& copy, const osg::CopyOp& op)
            : osg::Object(copy, op), SceneUtil::KeyframeController(copy, op),
              SceneUtil::NodeCallback<SplineTrack, NifOsg::MatrixTransform*>(copy, op),
              mData(copy.mData), mDefaults(copy.mDefaults), mHandles(copy.mHandles),
              mOffsets(copy.mOffsets), mRanges(copy.mRanges), mCount(copy.mCount),
              mStart(copy.mStart), mStop(copy.mStop), mCompact(copy.mCompact) {}
        META_Object(OpenOblivion, SplineTrack)
        osg::Callback* getAsCallback() override { return this; }
        Pose sample(float time) const
        {
            const float fraction = mStop > mStart ? (time - mStart) / (mStop - mStart) : 0.f;
            Pose out = mDefaults;
            if (auto p = channel<3>(0, fraction)) out.mTranslation = osg::Vec3f((*p)[0], (*p)[1], (*p)[2]);
            if (auto q = channel<4>(1, fraction))
            {
                // NIF control arrays store WXYZ; OSG quaternions are XYZW.
                osg::Quat rotation((*q)[1], (*q)[2], (*q)[3], (*q)[0]);
                const double length = rotation.length();
                if (length > 0 && std::isfinite(length)) out.mRotation = rotation / length;
                else out.mRotation.reset();
            }
            if (auto s = channel<1>(2, fraction)) out.mScale = (*s)[0];
            return out;
        }
        Pose getCurrentTransformation(osg::NodeVisitor* nv) override
        {
            return hasInput() ? sample(getInputValue(nv)) : Pose{};
        }
        osg::Vec3f getTranslation(float time) const override { return sample(time).mTranslation.value_or(osg::Vec3f{}); }
        void operator()(NifOsg::MatrixTransform* node, osg::NodeVisitor* nv)
        {
            const auto pose = getCurrentTransformation(nv);
            if (pose.mRotation) node->setRotation(*pose.mRotation);
            else node->setRotation(node->mRotationScale);
            if (pose.mTranslation) node->setTranslation(*pose.mTranslation);
            if (pose.mScale) node->setScale(*pose.mScale);
            traverse(node, nv);
        }
    private:
        template<std::size_t Dimensions> std::optional<std::array<float, Dimensions>> channel(std::size_t index, float fraction) const
        {
            if (!mData) return std::nullopt;
            if (mCompact) return splineChannel<Dimensions, std::int16_t>(mData->shorts, mHandles[index], mCount, fraction, mRanges[index], mOffsets[index]);
            return splineChannel<Dimensions, float>(mData->floats, mHandles[index], mCount, fraction);
        }
        std::shared_ptr<const SplineStorage> mData;
        Pose mDefaults;
        std::array<std::uint32_t, 3> mHandles{0xffffu, 0xffffu, 0xffffu};
        std::array<float, 3> mOffsets{}, mRanges{1.f, 1.f, 1.f};
        std::uint32_t mCount{0};
        float mStart{0}, mStop{0};
        bool mCompact{false};
    };

    inline std::string blockName(const Nif::ControlledBlock& block, const Nif::NiStringPalette* fallback = nullptr)
    {
        if (!block.mNodeName.empty()) return block.mNodeName;
        if (!block.mTargetName.empty()) return block.mTargetName;
        const auto* palette = block.mStringPalette.empty() ? fallback : block.mStringPalette.getPtr();
        if (!palette) return {};
        const auto value = paletteName(palette->mPalette, block.mNodeNameOffset);
        if (!value) throw std::runtime_error("Invalid sequence string-palette offset");
        return std::string(*value);
    }

    // Returns false only for the legacy root path, which the existing loader
    // still handles. Later-game roots are never mislabeled as legacy failures.
    inline bool loadSequence(Nif::FileView file, SceneUtil::KeyframeHolder& destination)
    {
        const Nif::NiControllerSequence* sequence = nullptr;
        for (std::size_t i = 0; i < file.numRoots(); ++i)
            if (const auto* candidate = dynamic_cast<const Nif::NiControllerSequence*>(file.getRoot(i)))
            {
                if (sequence) throw std::runtime_error("Multiple KF sequences require separate clip selection");
                sequence = candidate;
            }
        if (!sequence) return false;
        if (!std::isfinite(sequence->mStartTime) || !std::isfinite(sequence->mStopTime)
            || sequence->mStopTime < sequence->mStartTime || !std::isfinite(sequence->mFrequency))
            throw std::runtime_error("Invalid sequence timeline");
        SceneUtil::KeyframeHolder loaded;
        std::unordered_map<const Nif::NiBSplineData*, std::shared_ptr<const SplineStorage>> storage;
        std::size_t ignored = 0;
        for (const auto& block : sequence->mControlledBlocks)
        {
            if (block.mInterpolator.empty()) { ++ignored; continue; }
            const std::string name = blockName(block,
                sequence->mStringPalette.empty() ? nullptr : sequence->mStringPalette.getPtr());
            if (name.empty()) { ++ignored; continue; }
            osg::ref_ptr<SceneUtil::KeyframeController> callback;
            Nif::NiKeyframeController clock{};
            clock.mData = Nif::NiKeyframeDataPtr(nullptr);
            clock.mInterpolator = block.mInterpolator;
            clock.mFlags = 8 | (static_cast<unsigned>(Nif::NiTimeController::ExtrapolationMode::Constant) << 1);
            clock.mFrequency = sequence->mFrequency;
            clock.mPhase = file.getVersion() <= 0x0a040001u ? sequence->mPhase : 0.f;
            clock.mTimeStart = sequence->mStartTime;
            clock.mTimeStop = sequence->mStopTime;
            if (auto* ordinary = dynamic_cast<const Nif::NiTransformInterpolator*>(block.mInterpolator.getPtr()))
                callback = new TransformTrack(&clock, *ordinary);
            else if (auto* spline = dynamic_cast<const Nif::NiBSplineTransformInterpolator*>(block.mInterpolator.getPtr()))
            {
                std::shared_ptr<const SplineStorage> data;
                if (!spline->mSplineData.empty())
                {
                    const auto* source = spline->mSplineData.getPtr();
                    auto [entry, fresh] = storage.try_emplace(source);
                    if (fresh) entry->second = std::make_shared<SplineStorage>(SplineStorage{source->mFloatControlPoints, source->mCompactControlPoints});
                    data = entry->second;
                }
                callback = new SplineTrack(*spline, std::move(data));
            }
            else { ++ignored; continue; } // e.g. face/morph float tracks are a separate path
            callback->setFunction(std::make_shared<NifOsg::ControllerFunction>(&clock));
            if (!loaded.mKeyframeControllers.emplace(name, callback).second)
                throw std::runtime_error("Duplicate transform target in KF sequence: " + name);
        }
        std::string group = Misc::StringUtils::lowerCase(sequence->mName);
        if (group.empty()) throw std::runtime_error("Unnamed KF sequence");
        loaded.mTextKeys.emplace(sequence->mStartTime, group + ": start");
        loaded.mTextKeys.emplace(sequence->mStopTime, group + ": stop");
        if (!sequence->mTextKeys.empty())
            if (auto* keys = dynamic_cast<const Nif::NiTextKeyExtraData*>(sequence->mTextKeys.getPtr()))
                for (const auto& key : keys->mList)
                    loaded.mTextKeys.emplace(key.mTime, group + ": " + Misc::StringUtils::lowerCase(key.mText));
        destination.mKeyframeControllers = std::move(loaded.mKeyframeControllers);
        destination.mTextKeys = std::move(loaded.mTextKeys);
        Log(Debug::Info) << "OPENOBLIVION_KF sequence=" << sequence->mName << " tracks="
                        << destination.mKeyframeControllers.size() << " ignored_nontransform=" << ignored;
        return true;
    }
}
