// SPDX-License-Identifier: GPL-3.0-only
// Original native fixtures: separate embedded clips and authored box offsets.
#include "openoblivion_tes4_sequences.hpp"
#include <components/nifbullet/openoblivion_animated_boxes.hpp>
#include <components/resource/bulletshape.hpp>
#include <osg/CopyOp>
#include <iostream>

namespace
{
    void require(bool condition, const char* message)
    {
        if (!condition) throw std::runtime_error(message);
    }
    void near(double a, double b) { require(std::abs(a - b) < 0.00002, "Unexpected value"); }
    struct Clock : SceneUtil::ControllerSource
    {
        float getValue(osg::NodeVisitor*) override { return 0.f; }
    };
}

int main()
{
    using namespace OpenOblivion::Animation;
    Nif::NIFFile file{VFS::Path::Normalized("original-embedded-fixture.nif")};
    file.mVersion = 0x14000004;
    Nif::NiNode root{};
    root.mTransform = Nif::NiTransform::getIdentity();
    root.mCollision = Nif::NiCollisionObjectPtr(nullptr);
    Nif::NiControllerManager manager{};
    manager.mRecordType = Nif::RC_NiControllerManager;
    manager.mFlags = 8;
    manager.mNext = Nif::NiTimeControllerPtr(nullptr);
    root.mController = Nif::NiTimeControllerPtr(&manager);
    file.mRoots.push_back(&root);
    Nif::NiControllerSequence open{}, close{};
    open.mName = "Open"; close.mName = "Close";
    open.mStartTime = close.mStartTime = 0;
    open.mStopTime = close.mStopTime = 2;
    open.mStringPalette = close.mStringPalette = Nif::NiStringPalettePtr(nullptr);
    open.mTextKeys = close.mTextKeys = Nif::ExtraPtr(nullptr);
    Nif::NiTransformInterpolator first{}, second{};
    first.mData = second.mData = Nif::NiKeyframeDataPtr(nullptr);
    first.mDefaultValue.mTranslation.set(2, 3, 4);
    second.mDefaultValue.mTranslation.set(5, 6, 7);
    first.mDefaultValue.mRotation = second.mDefaultValue.mRotation = osg::Quat{};
    first.mDefaultValue.mScale = second.mDefaultValue.mScale = 1;
    Nif::ControlledBlock block{};
    block.mNodeName = "Original Target";
    block.mStringPalette = Nif::NiStringPalettePtr(nullptr);
    block.mInterpolator = Nif::NiInterpolatorPtr(&first);
    open.mControlledBlocks.push_back(block);
    block.mInterpolator = Nif::NiInterpolatorPtr(&second);
    close.mControlledBlocks.push_back(block);
    manager.mSequences.push_back(Nif::RecordPtrT<Nif::NiControllerSequence>(&open));
    manager.mSequences.push_back(Nif::RecordPtrT<Nif::NiControllerSequence>(&close));
    osg::ref_ptr<osg::Group> graph = new osg::Group;
    require(hasManagedController(root), "Active manager was missed");
    attachEmbeddedClips(file, *graph);
    const auto* clips = embeddedClips(*graph);
    require(clips && clips->clips.size() == 2, "Embedded sequences were merged or lost");
    require(clips->clips[0]->mTextKeys.hasGroupStart("open"), "Open timeline was lost");
    require(clips->clips[1]->mTextKeys.hasGroupStart("close"), "Close timeline was lost");
    auto copied = osg::clone(graph.get(), osg::CopyOp::DEEP_COPY_ALL);
    require(embeddedClips(*copied)->clips.size() == 2, "Scene clone lost its clips");
    auto clock = std::make_shared<Clock>();
    for (unsigned i = 0; i < 2; ++i)
    {
        auto track = osg::clone(clips->clips[i]->mKeyframeControllers.begin()->second.get(), osg::CopyOp::SHALLOW_COPY);
        track->setSource(clock);
        near(track->getCurrentTransformation(nullptr).mTranslation->x(), i == 0 ? 2 : 5);
    }
    manager.mFlags = 0;
    osg::ref_ptr<osg::Group> inactive = new osg::Group;
    attachEmbeddedClips(file, *inactive);
    require(!embeddedClips(*inactive) && !hasManagedController(root), "Inactive manager started clips");
    manager.mFlags = 8;
    file.mVersion = 0x14020007;
    attachEmbeddedClips(file, *inactive);
    require(!embeddedClips(*inactive), "Later-game format entered the classic adapter");
    file.mVersion = 0x14000004;
    close.mName = "OPEN";
    bool rejected = false;
    try { attachEmbeddedClips(file, *inactive); } catch (const std::runtime_error&) { rejected = true; }
    require(rejected && !embeddedClips(*inactive), "Duplicate group partially attached");

    Nif::NiNode leaf{};
    leaf.mTransform = Nif::NiTransform::getIdentity();
    leaf.mRecordIndex = 42;
    leaf.mController = Nif::NiTimeControllerPtr(nullptr);
    leaf.mTransform.mTranslation.set(11, 13, 17);
    root.mChildren.push_back(Nif::NiAVObjectPtr(&leaf));
    Nif::bhkCollisionObject collision{};
    collision.mRecordType = Nif::RC_bhkCollisionObject;
    collision.mFlags = 1;
    collision.mTarget = Nif::NiAVObjectPtr(&leaf);
    Nif::bhkRigidBody body{};
    body.mRecordType = Nif::RC_bhkRigidBodyT;
    body.mHavokFilter.mLayer = body.mInfo.mHavokFilter.mLayer = 2;
    body.mInfo.mMass = 0;
    body.mInfo.mMotionType = Nif::HkMotionType::Motion_Keyframed;
    body.mInfo.mQualityType = Nif::HkQualityType::Quality_Keyframed;
    body.mInfo.mTranslation.set(2, -1, 3, 0);
    body.mInfo.mRotation = osg::Quat{};
    Nif::bhkBoxShape box{};
    box.mRecordType = Nif::RC_bhkBoxShape;
    box.mExtents.set(2, 3, 4); box.mRadius = 0.1f;
    body.mShape = Nif::bhkShapePtr(&box);
    collision.mBody = Nif::bhkWorldObjectPtr(&body);
    leaf.mCollision = Nif::NiCollisionObjectPtr(&collision);
    std::unique_ptr<btCompoundShape, Resource::DeleteCollisionShape> compound;
    std::map<int, int> animated;
    require(OpenOblivion::Collision::addAnimatedBoxes(root, compound, animated), "Keyframed box was missed");
    require(animated.size() == 1 && animated.at(42) == 0, "Box lost its animated owning node");
    const auto* local = static_cast<const btCompoundShape*>(compound->getChildShape(0));
    const auto* bounds = static_cast<const btBoxShape*>(local->getChildShape(0));
    near(compound->getChildTransform(0).getOrigin().x(), 11);
    near(local->getChildTransform(0).getOrigin().x(), 14);
    near(local->getChildTransform(0).getOrigin().y(), -7);
    near(bounds->getHalfExtentsWithMargin().x(), 14);
    near(bounds->getHalfExtentsWithMargin().z(), 28);
    near(bounds->getMargin(), 0.7f);
    auto shape = std::make_shared<Resource::BulletShape>();
    shape->mCollisionShape = std::move(compound); shape->mAnimatedShapes = animated;
    auto instance = Resource::makeInstance(shape);
    require(instance->mCollisionShape.get() != shape->mCollisionShape.get(), "Reference shared mutable collision");
    auto* cloned = static_cast<btCompoundShape*>(instance->mCollisionShape.get());
    btTransform moved = cloned->getChildTransform(0); moved.setOrigin(btVector3(99, 0, 0));
    cloned->updateChildTransform(0, moved);
    near(static_cast<const btCompoundShape*>(shape->mCollisionShape.get())->getChildTransform(0).getOrigin().x(), 11);
    // A node scale is already represented in its local child shapes/offsets.
    // Preserve compound bookkeeping so a first update does not scale twice.
    leaf.mTransform.mScale = 2;
    compound.reset(); animated.clear();
    require(OpenOblivion::Collision::addAnimatedBoxes(root, compound, animated), "Scaled authored box was missed");
    auto scaled = std::make_shared<Resource::BulletShape>();
    scaled->mCollisionShape = std::move(compound); scaled->mAnimatedShapes = animated;
    auto scaledInstance = Resource::makeInstance(scaled);
    auto* outer = static_cast<btCompoundShape*>(scaledInstance->mCollisionShape.get());
    auto* scaledLocal = static_cast<btCompoundShape*>(outer->getChildShape(0));
    near(scaledLocal->getLocalScaling().x(), 2);
    near(scaledLocal->getChildTransform(0).getOrigin().x(), 28);
    scaledLocal->setLocalScaling(btVector3(2, 2, 2));
    near(scaledLocal->getChildTransform(0).getOrigin().x(), 28);
    leaf.mTransform.mScale = 1;
    // Unsupported/malformed bodies must leave an existing destination intact.
    compound.reset(new btCompoundShape);
    for (unsigned test = 0; test < 3; ++test)
    {
        body.mInfo.mMass = test == 0 ? 1.f : 0.f;
        box.mExtents.x() = test == 1 ? -1.f : 2.f;
        body.mInfo.mRotation = test == 2 ? osg::Quat(0, 0, 0, 0) : osg::Quat{};
        require(!OpenOblivion::Collision::addAnimatedBoxes(root, compound, animated), "Invalid authored box accepted");
        require(compound->getNumChildShapes() == 0, "Invalid box partially installed collision");
    }
    std::cout << "PASS embedded clip separation, cloning, names, version bounds and authored animated boxes\n";
}
