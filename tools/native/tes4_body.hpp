// SPDX-License-Identifier: GPL-3.0-only
// OpenOblivion: measured classic TES4 player controller hull.
//
// The vertices, convex radius and unit scale were read from the original
// executable's live player controller (Havok shape vtable 0xa99f28) on
// 2026-10-03; see docs/research/PLAYER_COLLISION_MODEL.md. They are Havok
// units and are converted by the executable's own 0.1428767293691635 factor.
// The shape is identical while standing, walking, jumping and sneaking and it
// rotates with the actor's heading. Bottom anchoring follows the host solver,
// which rests the lowest point one unit above the support surface.
#ifndef OPENMW_OPENOBLIVION_TES4_BODY_HPP
#define OPENMW_OPENOBLIVION_TES4_BODY_HPP

#include <BulletCollision/CollisionDispatch/btCollisionObject.h>
#include <BulletCollision/CollisionDispatch/btCollisionWorld.h>
#include <BulletCollision/CollisionShapes/btConvexHullShape.h>

#include <components/misc/constants.hpp>
#include <components/misc/convert.hpp>

#include "collisiontype.hpp"

#include <cstdlib>
#include <cstring>
#include <memory>

namespace OpenOblivion
{
    inline constexpr float sTes4HavokScale = 0.1428767293691635f;
    inline constexpr float sTes4BodyRing = 2.893253803253174f;
    inline constexpr float sTes4BodyDiagonal = 2.0458197593688965f;
    inline constexpr float sTes4BodyLowerRing = -4.614932060241699f;
    inline constexpr float sTes4BodyUpperRing = 7.697484016418457f;
    inline constexpr float sTes4BodyApex = 9.144110679626465f;
    inline constexpr float sTes4BodyRadius = 0.10000000149011612f;

    inline bool tes4OriginalBodyEnabled()
    {
        const char* value = std::getenv("OPENOBLIVION_ORIGINAL_BODY");
        return value != nullptr && std::strcmp(value, "1") == 0;
    }

    // Half extents in game units, including the convex radius.
    inline float tes4BodyHalfWidth()
    {
        return (sTes4BodyRing + sTes4BodyRadius) / sTes4HavokScale;
    }

    inline float tes4BodyHalfHeight()
    {
        return (sTes4BodyApex + sTes4BodyRadius) / sTes4HavokScale;
    }

    inline std::unique_ptr<btConvexHullShape> makeTes4PlayerBody()
    {
        const float r = sTes4BodyRing, d = sTes4BodyDiagonal;
        const float ring[8][2] = { { -r, 0 }, { -d, -d }, { -d, d }, { 0, -r }, { 0, r }, { d, -d }, { d, d }, { r, 0 } };
        auto shape = std::make_unique<btConvexHullShape>();
        // Set the margin first: the hull caches its bounds when the last point is added.
        shape->setMargin(sTes4BodyRadius / sTes4HavokScale);
        const btScalar scale = 1.0 / sTes4HavokScale;
        for (const auto& point : ring)
        {
            shape->addPoint(btVector3(point[0], point[1], sTes4BodyLowerRing) * scale, false);
            shape->addPoint(btVector3(point[0], point[1], sTes4BodyUpperRing) * scale, false);
        }
        shape->addPoint(btVector3(0, 0, -sTes4BodyApex) * scale, false);
        shape->addPoint(btVector3(0, 0, sTes4BodyApex) * scale, true);
        return shape;
    }

    // Only the measured TES4 body uses a convex hull for an actor.
    inline bool usesTes4Body(const btCollisionObject* object)
    {
        return object != nullptr && object->getCollisionShape() != nullptr
            && object->getCollisionShape()->getShapeType() == CONVEX_HULL_SHAPE_PROXYTYPE;
    }

    // The original controller reported its support as a horizontal contact
    // directly beneath the hull apex, while its cone rested on stair edges.
    // For the hull, walkability is therefore judged from the surface below the
    // centre rather than from the cone's steep edge contact. Other actors and
    // missing support keep the supplied contact normal.
    inline osg::Vec3f tes4SupportNormal(const btCollisionObject* actor, const btCollisionWorld* world,
        const osg::Vec3f& center, const osg::Vec3f& contactNormal)
    {
        if (!usesTes4Body(actor))
            return contactNormal;
        // Support extent includes local scaling and the margin exactly once;
        // Bullet's cached hull bounds add the margin a second time.
        const auto* shape = static_cast<const btConvexShape*>(actor->getCollisionShape());
        const btScalar apex = -shape->localGetSupportingVertex(btVector3(0, 0, -1)).z();
        const btScalar reach = apex + ::Constants::sStepSizeUp;
        const btVector3 from = Misc::Convert::toBullet(center);
        const btVector3 to = from - btVector3(0, 0, reach);
        btCollisionWorld::ClosestRayResultCallback callback(from, to);
        callback.m_collisionFilterGroup = MWPhysics::CollisionType_Actor;
        callback.m_collisionFilterMask
            = MWPhysics::CollisionType_World | MWPhysics::CollisionType_HeightMap | MWPhysics::CollisionType_Door;
        world->rayTest(from, to, callback);
        if (!callback.hasHit())
            return contactNormal;
        return Misc::Convert::toOsg(callback.m_hitNormalWorld);
    }
}

#endif
