// SPDX-License-Identifier: GPL-3.0-only
// Original in-memory fixtures for the audited native KF adapter. No game data.
// Compile against the same Release components library as the native engine.
#include "openoblivion_tes4_kf.hpp"
#include "openoblivion_tes4_skin.hpp"
#include <components/nif/niffile.hpp>
#include <osg/CopyOp>
#include <iostream>

namespace
{
    void require(bool condition, const char* message)
    {
        if (!condition) throw std::runtime_error(message);
    }
    void near(double a, double b) { require(std::abs(a - b) < 0.00002, "Unexpected sampled value"); }
    struct Clock : SceneUtil::ControllerSource
    {
        float time = 0;
        float getValue(osg::NodeVisitor*) override { return time; }
    };
    template<class F> void rejects(F&& operation)
    {
        bool rejected = false;
        try { operation(); } catch (const std::runtime_error&) { rejected = true; }
        require(rejected, "Invalid fixture was accepted");
    }
}

int main()
{
    using namespace OpenOblivion::Animation;
    // An empty generic attachment filter used to clone the whole donor
    // skeleton. The TES4 selector must select the local renderable subtree.
    osg::ref_ptr<SceneUtil::Skeleton> donor = new SceneUtil::Skeleton;
    osg::ref_ptr<osg::MatrixTransform> bindBone = new osg::MatrixTransform;
    osg::ref_ptr<osg::MatrixTransform> mesh = new osg::MatrixTransform;
    osg::ref_ptr<SceneUtil::RigGeometry> rig = new SceneUtil::RigGeometry;
    donor->addChild(bindBone); donor->addChild(mesh); mesh->addChild(rig);
    OpenOblivion::Skin::Parts selected;
    donor->accept(selected);
    require(selected.renderables.size() == 1 && selected.renderables.contains(mesh.get()),
        "Part selector copied a donor skeleton or lost a rig");
    Nif::NIFFile file{VFS::Path::Normalized("original-fixture.kf")};
    file.mVersion = 0x14000004;
    Nif::NiControllerSequence sequence{};
    sequence.mName = "Fixture";
    sequence.mStartTime = 0;
    sequence.mStopTime = 2;
    sequence.mTextKeys = Nif::ExtraPtr(nullptr);
    sequence.mStringPalette = Nif::NiStringPalettePtr(nullptr);
    file.mRoots.push_back(&sequence);
    Nif::NiTransformInterpolator constant{};
    constant.mRecordType = Nif::RC_NiTransformInterpolator;
    constant.mData = Nif::NiKeyframeDataPtr(nullptr);
    constant.mDefaultValue.mTranslation.set(3, 4, 5);
    constant.mDefaultValue.mRotation = osg::Quat(0, 0, 0, 1);
    constant.mDefaultValue.mScale = 2;
    Nif::ControlledBlock block{};
    block.mNodeName = "Original Bone";
    block.mInterpolator = Nif::NiInterpolatorPtr(&constant);
    block.mStringPalette = Nif::NiStringPalettePtr(nullptr);
    sequence.mControlledBlocks.push_back(block);
    SceneUtil::KeyframeHolder holder;
    require(loadSequence(file, holder), "Sequence root was missed");
    require(holder.mKeyframeControllers.size() == 1, "Constant track was dropped");
    require(holder.mTextKeys.hasGroupStart("fixture"), "Sequence group was missed");
    osg::ref_ptr<SceneUtil::KeyframeController> track
        = osg::clone(holder.mKeyframeControllers.begin()->second.get(), osg::CopyOp::SHALLOW_COPY);
    auto clock = std::make_shared<Clock>();
    track->setSource(clock);
    auto pose = track->getCurrentTransformation(nullptr);
    require(pose.mTranslation && pose.mRotation && pose.mScale, "Constant defaults were lost");
    near(pose.mTranslation->x(), 3); near(pose.mRotation->w(), 1); near(*pose.mScale, 2);
    near(track->getTranslation(1).z(), 5);

    // A static absent component uses the file's invalid-value sentinel.
    constant.mDefaultValue.mScale = -std::numeric_limits<float>::max();
    loadSequence(file, holder);
    track = osg::clone(holder.mKeyframeControllers.begin()->second.get(), osg::CopyOp::SHALLOW_COPY);
    track->setSource(clock);
    require(!track->getCurrentTransformation(nullptr).mScale, "Sentinel became a scale");

    // Palette fallback and failure must leave the previously loaded holder intact.
    Nif::NiStringPalette palette{};
    palette.mPalette = std::string("Palette Bone\0", 13);
    sequence.mStringPalette = Nif::NiStringPalettePtr(&palette);
    sequence.mControlledBlocks[0].mNodeName.clear();
    sequence.mControlledBlocks[0].mNodeNameOffset = 0;
    loadSequence(file, holder);
    require(holder.mKeyframeControllers.contains("Palette Bone"), "Palette target was missed");
    sequence.mControlledBlocks[0].mNodeNameOffset = 100;
    rejects([&] { loadSequence(file, holder); });
    require(holder.mKeyframeControllers.contains("Palette Bone"), "Failed load replaced good clip");
    sequence.mControlledBlocks[0].mNodeNameOffset = 0;
    sequence.mControlledBlocks.push_back(sequence.mControlledBlocks[0]);
    rejects([&] { loadSequence(file, holder); });
    sequence.mControlledBlocks.pop_back();

    // Analytic four-point spline in WXYZ and interleaved XYZ layout. The clone
    // must survive destruction of its owner NIF data and retain its own clock.
    osg::ref_ptr<SplineTrack> spline;
    {
        Nif::NiBSplineBasisData basis{};
        basis.mNumControlPoints = 4;
        Nif::NiBSplineCompTransformInterpolator interp{};
        interp.mBasisData = Nif::NiBSplineBasisDataPtr(&basis);
        interp.mStartTime = 0; interp.mStopTime = 2;
        interp.mTranslationHandle = 0; interp.mRotationHandle = 12; interp.mScaleHandle = 0xffff;
        interp.mTranslationOffset = 0; interp.mTranslationHalfRange = 1;
        interp.mRotationOffset = 0; interp.mRotationHalfRange = 1;
        interp.mValue.mScale = 1;
        auto data = std::make_shared<SplineStorage>();
        data->shorts = {0,0,0, 10922,0,0, 21845,0,0, 32767,0,0,
            32767,0,0,0, 32767,0,0,0, 32767,0,0,0, 32767,0,0,0};
        spline = new SplineTrack(interp, data);
        spline->setSource(clock);
        clock->time = 1;
        auto sampled = spline->getCurrentTransformation(nullptr);
        near(sampled.mTranslation->x(), .5); near(sampled.mRotation->w(), 1);
        near(sampled.mRotation->x(), 0); near(*sampled.mScale, 1);
        interp.mRotationHandle = 1000;
        rejects([&] { osg::ref_ptr<SplineTrack> invalid = new SplineTrack(interp, data); });
    }
    osg::ref_ptr<SplineTrack> clone = osg::clone(spline.get(), osg::CopyOp::SHALLOW_COPY);
    auto cloneClock = std::make_shared<Clock>();
    clone->setSource(cloneClock);
    near(clone->getCurrentTransformation(nullptr).mTranslation->x(), 0);
    near(spline->getCurrentTransformation(nullptr).mTranslation->x(), .5);
    near(spline->sample(-10).mTranslation->x(), 0);
    near(spline->sample(10).mTranslation->x(), 1);
    sequence.mStopTime = -1;
    rejects([&] { loadSequence(file, holder); });
    file.mRoots.clear();
    require(!loadSequence(file, holder), "Legacy fallback was swallowed");
    std::cout << "Native original KF defaults, palette, spline, clone, lifetime and rejection fixtures passed\n";
}
