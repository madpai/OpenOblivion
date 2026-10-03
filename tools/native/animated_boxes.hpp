// SPDX-License-Identifier: GPL-3.0-only
// Original bounded TES4 keyframed-box collision adapter. No Havok bytecode.
#pragma once
#include <components/nif/physics.hpp>
#include <components/nif/node.hpp>
#include <components/resource/bulletshape.hpp>
#include <components/misc/convert.hpp>
#include <BulletCollision/CollisionShapes/btBoxShape.h>
#include <BulletCollision/CollisionShapes/btCompoundShape.h>
#include <algorithm>
#include <cmath>
#include <map>
#include <memory>
#include <optional>
#include <unordered_set>
#include <vector>

namespace OpenOblivion::Collision
{
    // Measured classic TES4 primitive units. Fixed strips deliberately keep
    // their existing mesh-unit path; this conversion applies only to boxes.
    inline constexpr float boxUnits = 7.f;
    struct AnimatedBox
    {
        unsigned record;
        osg::Matrixf nodeTransform;
        osg::Vec3f extents, offset;
        osg::Quat rotation;
        float radius;
    };

    inline std::optional<std::vector<AnimatedBox>> animatedBoxes(const Nif::NiAVObject& root)
    {
        struct Pending { const Nif::NiAVObject* node; osg::Matrixf parent; };
        std::vector<Pending> pending{{&root, osg::Matrixf{}}};
        std::unordered_set<const Nif::NiAVObject*> visited;
        std::vector<AnimatedBox> result;
        while (!pending.empty())
        {
            const auto item = pending.back(); pending.pop_back();
            if (!visited.insert(item.node).second) return std::nullopt;
            const auto& node = *item.node;
            const osg::Matrixf matrix = node.mTransform.toMatrix() * item.parent;
            for (unsigned row = 0; row < 4; ++row)
                for (unsigned col = 0; col < 4; ++col)
                    if (!std::isfinite(matrix(row, col))) return std::nullopt;
            if (!node.mCollision.empty())
            {
                const auto* collision = dynamic_cast<const Nif::bhkCollisionObject*>(node.mCollision.getPtr());
                if (!collision || collision->mRecordType != Nif::RC_bhkCollisionObject
                    || !(collision->mFlags & 1)
                    || collision->mTarget.empty() || collision->mTarget.getPtr() != &node
                    || collision->mBody.empty() || collision->mBody->mRecordType != Nif::RC_bhkRigidBodyT)
                    return std::nullopt;
                const auto* body = static_cast<const Nif::bhkRigidBody*>(collision->mBody.getPtr());
                if (body->mHavokFilter.mLayer != 2 || body->mInfo.mHavokFilter.mLayer != 2
                    || body->mInfo.mMotionType != Nif::HkMotionType::Motion_Keyframed
                    || body->mInfo.mQualityType != Nif::HkQualityType::Quality_Keyframed
                    || body->mInfo.mMass != 0 || body->mShape.empty()
                    || body->mShape->mRecordType != Nif::RC_bhkBoxShape) return std::nullopt;
                const auto* box = static_cast<const Nif::bhkBoxShape*>(body->mShape.getPtr());
                AnimatedBox value{node.mRecordIndex, matrix, box->mExtents * boxUnits,
                    osg::Vec3f(body->mInfo.mTranslation.x(), body->mInfo.mTranslation.y(), body->mInfo.mTranslation.z()) * boxUnits,
                    body->mInfo.mRotation, box->mRadius * boxUnits};
                for (unsigned axis = 0; axis < 3; ++axis)
                    if (!std::isfinite(value.extents[axis]) || value.extents[axis] <= 0
                        || !std::isfinite(value.offset[axis])) return std::nullopt;
                if (!std::isfinite(value.radius) || value.radius < 0
                    || !std::isfinite(value.rotation.length2()) || value.rotation.length2() <= 0)
                    return std::nullopt;
                value.rotation /= value.rotation.length();
                if (value.radius >= std::min({value.extents.x(), value.extents.y(), value.extents.z()})) return std::nullopt;
                result.push_back(value);
            }
            if (const auto* parent = dynamic_cast<const Nif::NiNode*>(&node))
                for (const auto& child : parent->mChildren)
                    if (!child.empty()) pending.push_back({child.getPtr(), matrix});
        }
        if (result.empty()) return std::nullopt;
        return result;
    }

    inline bool addAnimatedBoxes(const Nif::NiAVObject& root,
        std::unique_ptr<btCompoundShape, Resource::DeleteCollisionShape>& compound,
        std::map<int, int>& animated)
    {
        const auto boxes = animatedBoxes(root);
        if (!boxes) return false; // No partial shape is installed on failure.
        if (!compound) compound.reset(new btCompoundShape);
        for (const auto& box : *boxes)
        {
            // Keep the authored body offset inside a local compound. The outer
            // child is driven by the owner's animated NiNode transform.
            std::unique_ptr<btCompoundShape, Resource::DeleteCollisionShape> local(new btCompoundShape);
            auto shape = std::make_unique<btBoxShape>(Misc::Convert::toBullet(box.extents));
            shape->setMargin(box.radius);
            btTransform body;
            body.setIdentity(); body.setOrigin(Misc::Convert::toBullet(box.offset));
            body.setRotation(Misc::Convert::toBullet(box.rotation));
            local->addChildShape(body, shape.release());
            osg::Matrixf matrix = box.nodeTransform;
            local->setLocalScaling(Misc::Convert::toBullet(matrix.getScale()));
            matrix.orthoNormalize(matrix);
            btTransform transform; transform.setIdentity();
            transform.setOrigin(Misc::Convert::toBullet(matrix.getTrans()));
            for (int row = 0; row < 3; ++row)
                for (int col = 0; col < 3; ++col) transform.getBasis()[row][col] = matrix(col, row);
            animated.emplace(box.record, compound->getNumChildShapes());
            compound->addChildShape(transform, local.release());
        }
        return true;
    }
}
