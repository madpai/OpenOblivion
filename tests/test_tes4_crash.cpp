// SPDX-License-Identifier: GPL-3.0-only
// The crash log writes a backtrace for a native fault, then the process still dies.
#include "tes4_crash.hpp"

#include <cstdio>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

#include <sys/wait.h>

__attribute__((noinline)) static void fault(volatile int* where)
{
    *where = 1;
}

int main()
{
    const std::string path = "oo_crash_log_test.txt";
    std::remove(path.c_str());
    const pid_t child = ::fork();
    if (child == 0)
    {
        ::setenv("OPENOBLIVION_CRASH_LOG", path.c_str(), 1);
        OpenOblivion::tes4InstallCrashLog();
        fault(nullptr);
        return 0;
    }
    int status = 0;
    ::waitpid(child, &status, 0);
    std::ifstream in(path);
    std::stringstream text;
    text << in.rdbuf();
    const std::string log = text.str();
    std::remove(path.c_str());
    if (!WIFSIGNALED(status) || WTERMSIG(status) != SIGSEGV)
    {
        std::cerr << "the child should still die from SIGSEGV\n";
        return 1;
    }
    if (log.find("OPENOBLIVION_CRASH signal=11") == std::string::npos || log.find("#0 ") == std::string::npos)
    {
        std::cerr << "no backtrace written: " << log << '\n';
        return 1;
    }
    std::cout << "TES4 crash log fixture passed\n";
    return 0;
}
