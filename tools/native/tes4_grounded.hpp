// SPDX-License-Identifier: GPL-3.0-only
// OpenOblivion: applies the classic TES4 grounded motion law (openoblivion_tes4_grounded_law.hpp) around the
// host's movement solver for the player. The solver keeps doing what it does (horizontal collision, stepping up,
// walls); this runs after it and replaces only the vertical outcome: no snap down to the ground, the original's
// support range, hover, capture and fall instead.
#ifndef OPENMW_OPENOBLIVION_TES4_GROUNDED_HPP
#define OPENMW_OPENOBLIVION_TES4_GROUNDED_HPP

#include <BulletCollision/BroadphaseCollision/btBroadphaseProxy.h>
#include <BulletCollision/CollisionDispatch/btCollisionObject.h>
#include <BulletCollision/CollisionDispatch/btCollisionWorld.h>

#include <osg/Math>
#include <osg/Vec3f>

#include <components/debug/debuglog.hpp>
#include <components/misc/constants.hpp>

#include <cmath>

#include "collisiontype.hpp"
#include "movementsolver.hpp"
#include "openoblivion_tes4_grounded_law.hpp"
#include "physicssystem.hpp"
#include "trace.h"

namespace OpenOblivion
{
    inline bool tes4WalkableNormal(const osg::Vec3f& normal)
    {
        static const float sMaxSlopeCos = std::cos(osg::DegreesToRadians(Constants::sMaxSlope));
        return normal.z() > sMaxSlopeCos;
    }

    inline void tes4GroundedMove(MWPhysics::ActorFrameData& actor, float time, const btCollisionWorld* world,
        const MWPhysics::WorldFrameData& worldData)
    {
        using namespace MWPhysics;
        const int mode = tes4GroundedMode();
        static const bool announced = [mode] {
            if (mode != 0)
                Log(Debug::Info) << "OpenOblivion TES4 grounded motion: mode " << mode;
            return true;
        }();
        (void)announced;
        if (mode == 0 || !actor.mIsPlayer || actor.mSkipCollisionDetection || actor.mFlying || actor.mInert
            || actor.mPosition.z() < actor.mSwimLevel)
        {
            MovementSolver::move(actor, time, world, worldData);
            return;
        }

        const bool wasSupported = actor.mIsOnGround && !actor.mIsOnSlope;
        const float vzUsed = actor.mInertia.z();
        const float zPre = actor.mPosition.z();
        const bool takeoff = actor.mMovement.z() > 0.f && wasSupported;
        MovementSolver::move(actor, time, world, worldData);
        // A takeoff, a steep slope found by the host, or swimming: the host's result stands.
        if (takeoff || actor.mIsOnSlope || actor.mPosition.z() < actor.mSwimLevel)
            return;

        // Height after the horizontal solve: the host snaps a grounded hull down to the ground, which the original
        // does not do, so a hull that was supported takes the height it had (or the height it stepped up to). The
        // horizontal path was traced at that height, so the hull is free there; no extra sweep upward is needed.
        // The sweep below keeps the hull out of the ground for the vertical move of this step.
        const float zSolver = actor.mPosition.z();
        const float z0 = wasSupported ? (zSolver > zPre + 0.01f ? zSolver : zPre) : zSolver;

        // Sweep the hull down from there, in the host's hull-centre coordinates.
        const float reach = tes4GroundReach(wasSupported, vzUsed, time);
        const osg::Vec3f from(actor.mPosition.x(), actor.mPosition.y(), z0 + actor.mHalfExtentsZ);
        const osg::Vec3f to = from - osg::Vec3f(0.f, 0.f, reach);
        ActorTracer tracer;
        tracer.doTrace(actor.mCollisionObject, from, to, world);

        Tes4GroundQuery surface;
        const btCollisionObject* hit = nullptr;
        if (tracer.mFraction < 1.f && tracer.mHitObject != nullptr)
        {
            const int group = tracer.mHitObject->getBroadphaseHandle()->m_collisionFilterGroup;
            if (group != CollisionType_Actor && group != CollisionType_Water)
            {
                surface.found = true;
                surface.restZ = tracer.mEndPos.z() + sTes4RestOffset - actor.mHalfExtentsZ;
                surface.contact = tes4WalkableNormal(tracer.mPlaneNormal) ? Tes4Contact::Walkable : Tes4Contact::Steep;
                hit = tracer.mHitObject;
            }
        }
        // Mode 1 only models walkable ground; a steep contact keeps the host's stair and slope handling.
        if (mode == 1 && surface.found && surface.contact == Tes4Contact::Steep)
            return;

        const Tes4GroundResult result = tes4GroundStep(wasSupported, z0, vzUsed, time, actor.mSlowFall, surface, time);
        // Airborne before and after: the host already integrated this step.
        if (!wasSupported && !result.supported)
            return;

        actor.mPosition.z() = result.z;
        actor.mIsOnSlope = false;
        if (result.supported)
        {
            actor.mIsOnGround = true;
            actor.mStandingOn = hit;
            actor.mInertia = osg::Vec3f(0.f, 0.f, result.vz);
        }
        else
        {
            actor.mIsOnGround = false;
            actor.mStandingOn = nullptr;
            actor.mInertia.z() = result.vz;
        }
    }
}

#endif
