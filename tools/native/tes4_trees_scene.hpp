// SPDX-License-Identifier: GPL-3.0-only
// OpenOblivion: scene-graph side of the TES4 tree billboards.
// See tes4_trees.hpp and docs/research/TES4_TREES.md.
#ifndef OPENMW_OPENOBLIVION_TES4_TREES_SCENE_HPP
#define OPENMW_OPENOBLIVION_TES4_TREES_SCENE_HPP

#include <string>

#include <osg/AlphaFunc>
#include <osg/Geometry>
#include <osg/Group>
#include <osg/Texture2D>

// The newer engine feeds shader material uniforms from SceneUtil::Material; the older
// Android donor reads osg::Material. A material of the wrong kind leaves the uniforms unset.
#if __has_include(<components/sceneutil/material.hpp>)
#include <components/sceneutil/material.hpp>
#define OPENOBLIVION_SCENEUTIL_MATERIAL 1
#else
#include <osg/Material>
#endif

#include <components/debug/debuglog.hpp>
#include <components/resource/imagemanager.hpp>
#include <components/vfs/manager.hpp>
#include <components/vfs/pathutil.hpp>

#include <components/misc/openoblivion_tes4_trees.hpp>

namespace OpenOblivion
{
    // Used when a TREE record carried no BNAM (none of the master's do).
    inline constexpr float sTreeFallbackSize = 1200.f;
    // Alpha cut-off of the original billboards' leaf edges.
    inline constexpr float sTreeAlphaCutoff = 0.5f;

    inline osg::ref_ptr<osg::Geometry> makeTreeQuad(
        const osg::Vec3f& right, float width, float height, osg::Texture2D* texture)
    {
        osg::ref_ptr<osg::Geometry> geometry(new osg::Geometry);
        geometry->setSupportsDisplayList(false);
        geometry->setUseDisplayList(false);
        geometry->setUseVertexBufferObjects(true);

        const osg::Vec3f half = right * (width * 0.5f);
        osg::ref_ptr<osg::Vec3Array> vertices(new osg::Vec3Array);
        vertices->push_back(-half);
        vertices->push_back(half);
        vertices->push_back(half + osg::Vec3f(0.f, 0.f, height));
        vertices->push_back(-half + osg::Vec3f(0.f, 0.f, height));
        geometry->setVertexArray(vertices);

        // Foliage is lit from above on both faces, as the original's tree
        // shading is not directional per face.
        osg::ref_ptr<osg::Vec3Array> normals(new osg::Vec3Array(4));
        for (osg::Vec3f& normal : *normals)
            normal = osg::Vec3f(0.f, 0.f, 1.f);
        geometry->setNormalArray(normals, osg::Array::BIND_PER_VERTEX);

        // OpenMW flips DDS images on load so that v = 0 is the picture's top.
        osg::ref_ptr<osg::Vec2Array> uvs(new osg::Vec2Array);
        uvs->push_back(osg::Vec2f(0.f, 1.f));
        uvs->push_back(osg::Vec2f(1.f, 1.f));
        uvs->push_back(osg::Vec2f(1.f, 0.f));
        uvs->push_back(osg::Vec2f(0.f, 0.f));
        geometry->setTexCoordArray(0, uvs, osg::Array::BIND_PER_VERTEX);

        osg::ref_ptr<osg::Vec4Array> colors(new osg::Vec4Array);
        colors->push_back(osg::Vec4f(1.f, 1.f, 1.f, 1.f));
        geometry->setColorArray(colors, osg::Array::BIND_OVERALL);

        osg::ref_ptr<osg::DrawElementsUShort> indices(new osg::DrawElementsUShort(GL_TRIANGLES));
        for (unsigned short index : { 0, 1, 2, 0, 2, 3 })
            indices->push_back(index);
        geometry->addPrimitiveSet(indices);

        // The original lights trees by sun and ambient only. Without this, a billboard's
        // large bounds pick up every nearby point light (blue Ayleid glows turn a yew blue).
        geometry->setUserValue("simpleLighting", true);

        osg::StateSet* state = geometry->getOrCreateStateSet();
        state->setTextureAttributeAndModes(0, texture, osg::StateAttribute::ON);
        return geometry;
    }

    // Returns null when the tree has no billboard image.
    inline osg::ref_ptr<osg::Node> loadTreeBillboard(
        VFS::Path::NormalizedView sptPath, const VFS::Manager* vfs, Resource::ImageManager* imageManager)
    {
        const std::string key = treeKey(sptPath.value());
        const VFS::Path::Normalized texturePath("textures/trees/billboards/" + key + ".dds");
        if (!vfs->exists(texturePath))
        {
            Log(Debug::Warning) << "No billboard image for SpeedTree model " << sptPath;
            return nullptr;
        }

        TreeBillboardSize size;
        if (!findTreeSize(sptPath.value(), size))
        {
            Log(Debug::Warning) << "No BNAM size for SpeedTree model " << sptPath << ", using the fallback size";
            size = TreeBillboardSize{ sTreeFallbackSize, sTreeFallbackSize };
        }

        osg::ref_ptr<osg::Texture2D> texture(new osg::Texture2D(imageManager->getImage(texturePath)));
        texture->setWrap(osg::Texture::WRAP_S, osg::Texture::CLAMP_TO_EDGE);
        texture->setWrap(osg::Texture::WRAP_T, osg::Texture::CLAMP_TO_EDGE);
        texture->setResizeNonPowerOfTwoHint(false);

        osg::ref_ptr<osg::Group> root(new osg::Group);
        root->setName("OpenOblivionTreeBillboard");
        root->setUserValue("simpleLighting", true);
        root->addChild(makeTreeQuad(osg::Vec3f(1.f, 0.f, 0.f), size.mWidth, size.mHeight, texture));
        root->addChild(makeTreeQuad(osg::Vec3f(0.f, 1.f, 0.f), size.mWidth, size.mHeight, texture));

        osg::StateSet* state = root->getOrCreateStateSet();
#ifdef OPENOBLIVION_SCENEUTIL_MATERIAL
        osg::ref_ptr<SceneUtil::Material> material(new SceneUtil::Material);
        material->setVertexColorMode(SceneUtil::VertexColorModes::None);
        material->setDiffuse(osg::Vec4f(1.f, 1.f, 1.f, 1.f));
        material->setAmbient(osg::Vec4f(1.f, 1.f, 1.f, 1.f));
        material->setSpecular(osg::Vec4f(0.f, 0.f, 0.f, 1.f));
        material->setEmission(osg::Vec4f(0.f, 0.f, 0.f, 1.f));
#else
        osg::ref_ptr<osg::Material> material(new osg::Material);
        material->setColorMode(osg::Material::OFF);
        material->setAmbient(osg::Material::FRONT_AND_BACK, osg::Vec4f(1.f, 1.f, 1.f, 1.f));
        material->setDiffuse(osg::Material::FRONT_AND_BACK, osg::Vec4f(1.f, 1.f, 1.f, 1.f));
        material->setSpecular(osg::Material::FRONT_AND_BACK, osg::Vec4f(0.f, 0.f, 0.f, 1.f));
        material->setEmission(osg::Material::FRONT_AND_BACK, osg::Vec4f(0.f, 0.f, 0.f, 1.f));
#endif
        state->setAttributeAndModes(material, osg::StateAttribute::ON);
        state->setAttributeAndModes(new osg::AlphaFunc(osg::AlphaFunc::GREATER, sTreeAlphaCutoff));
        return root;
    }
}

#endif
