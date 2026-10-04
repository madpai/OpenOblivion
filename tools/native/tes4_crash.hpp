// SPDX-License-Identifier: GPL-3.0-only
// OpenOblivion: leave a backtrace behind when the game thread crashes natively.
//
// A native crash on the phone otherwise ends the scene with no message. With
// OPENOBLIVION_CRASH_LOG set to a file path, the first call to
// tes4InstallCrashLog() on the game thread installs handlers for SIGSEGV,
// SIGBUS, SIGABRT, SIGILL and SIGFPE that append the signal, fault address and a
// backtrace (module, offset, symbol) to that file, then pass the signal on to
// whatever handled it before (the Android runtime keeps working). Only faults
// on the thread that installed it are logged: managed runtime threads fault by
// design. Resolve offsets with the matching, unstripped native library.
#ifndef OPENMW_OPENOBLIVION_TES4_CRASH_HPP
#define OPENMW_OPENOBLIVION_TES4_CRASH_HPP

#include <csignal>
#include <cstdint>
#include <initializer_list>
#include <cstdio>
#include <cstdlib>
#include <cstring>

#include <dlfcn.h>
#include <fcntl.h>
#include <unistd.h>
#include <unwind.h>

#include <sys/syscall.h>

namespace OpenOblivion
{
    namespace Crash
    {
        struct State
        {
            char path[512] = {};
            long thread = -1;
            struct sigaction previous[32] = {};
        };

        inline State& state()
        {
            static State instance;
            return instance;
        }

        struct Trace
        {
            int count = 0;
            void* pcs[48] = {};
        };

        inline _Unwind_Reason_Code step(struct _Unwind_Context* context, void* argument)
        {
            Trace& trace = *static_cast<Trace*>(argument);
            const uintptr_t pc = _Unwind_GetIP(context);
            if (pc == 0 || trace.count >= 48)
                return _URC_END_OF_STACK;
            trace.pcs[trace.count++] = reinterpret_cast<void*>(pc);
            return _URC_NO_REASON;
        }

        inline void handle(int signal, siginfo_t* info, void* context)
        {
            State& crash = state();
            static volatile sig_atomic_t writing = 0;
            if (static_cast<long>(::syscall(SYS_gettid)) == crash.thread && !writing)
            {
                writing = 1;
                const int fd = ::open(crash.path, O_WRONLY | O_CREAT | O_APPEND, 0600);
                if (fd >= 0)
                {
                    ::dprintf(fd, "OPENOBLIVION_CRASH signal=%d address=%p\n", signal, info != nullptr ? info->si_addr : nullptr);
                    Trace trace;
                    _Unwind_Backtrace(step, &trace);
                    for (int i = 0; i < trace.count; ++i)
                    {
                        Dl_info where;
                        if (::dladdr(trace.pcs[i], &where) != 0 && where.dli_fname != nullptr)
                            ::dprintf(fd, "  #%d %s+0x%lx %s\n", i, where.dli_fname,
                                static_cast<unsigned long>(static_cast<const char*>(trace.pcs[i])
                                    - static_cast<const char*>(where.dli_fbase)),
                                where.dli_sname != nullptr ? where.dli_sname : "");
                        else
                            ::dprintf(fd, "  #%d %p\n", i, trace.pcs[i]);
                    }
                    ::close(fd);
                }
            }
            // Pass on to the previous handler (or the default action, which ends the process).
            const struct sigaction& old = crash.previous[signal];
            if ((old.sa_flags & SA_SIGINFO) != 0 && old.sa_sigaction != nullptr)
                old.sa_sigaction(signal, info, context);
            else if (old.sa_handler != SIG_DFL && old.sa_handler != SIG_IGN && old.sa_handler != nullptr)
                old.sa_handler(signal);
            else
            {
                ::signal(signal, SIG_DFL);
                ::raise(signal);
            }
        }
    }

    // Idempotent; call it from the thread that runs the game.
    inline void tes4InstallCrashLog()
    {
        static bool installed = false;
        if (installed)
            return;
        installed = true;
        const char* path = std::getenv("OPENOBLIVION_CRASH_LOG");
        if (path == nullptr || *path == '\0' || std::strlen(path) >= sizeof(Crash::State::path))
            return;
        Crash::State& crash = Crash::state();
        std::strcpy(crash.path, path);
        crash.thread = static_cast<long>(::syscall(SYS_gettid));
        // An alternate stack lets the handler run after a stack overflow.
        static char alternate[64 * 1024];
        stack_t stack = {};
        stack.ss_sp = alternate;
        stack.ss_size = sizeof(alternate);
        ::sigaltstack(&stack, nullptr);
        struct sigaction action = {};
        action.sa_sigaction = Crash::handle;
        action.sa_flags = SA_SIGINFO | SA_ONSTACK;
        ::sigemptyset(&action.sa_mask);
        for (const int signal : { SIGSEGV, SIGBUS, SIGABRT, SIGILL, SIGFPE })
            ::sigaction(signal, &action, &crash.previous[signal]);
    }
}

#endif
