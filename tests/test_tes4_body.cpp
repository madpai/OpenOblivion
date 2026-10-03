// SPDX-License-Identifier: GPL-3.0-only
#include "tes4_body.hpp"

#include <BulletCollision/BroadphaseCollision/btDbvtBroadphase.h>
#include <BulletCollision/CollisionDispatch/btDefaultCollisionConfiguration.h>
#include <BulletCollision/CollisionShapes/btBoxShape.h>

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <memory>

static int checks = 0;

static void require(bool value, const char* message)
{
    ++checks;
    if (!value)
    {
        std::cerr << message << '\n';
        std::exit(1);
    }
}

static bool near(double a, double b, double tolerance = 1e-3)
{
    return std::abs(a - b) <= tolerance;
}

struct World
{
    btDefaultCollisionConfiguration configuration;
    btCollisionDispatcher dispatcher{ &configuration };
    btDbvtBroadphase broadphase;
    btCollisionWorld world{ &dispatcher, &broadphase, &configuration };
};

int main()
{
    // Game-unit values recovered from the measured Havok hull and scale.
    require(near(OpenOblivion::sTes4BodyRing / OpenOblivion::sTes4HavokScale, 20.25), "ring radius is 20.25 units");
    require(near(OpenOblivion::sTes4BodyApex / OpenOblivion::sTes4HavokScale, 64.0), "apex is 64 units from centre");
    require(near(OpenOblivion::sTes4BodyLowerRing / OpenOblivion::sTes4HavokScale, -32.3001), "lower ring");
    require(near(OpenOblivion::sTes4BodyUpperRing / OpenOblivion::sTes4HavokScale, 53.875), "upper ring");
    // The executable's diagonal vertices sit 1.96e-5 Havok units inside the
    // exact ring, which reflects its own cos(45 degrees) rounding.
    require(near(OpenOblivion::sTes4BodyDiagonal, OpenOblivion::sTes4BodyRing * std::sqrt(0.5), 3e-5),
        "octagon diagonal vertices lie on the ring");
    require(near(OpenOblivion::tes4BodyHalfWidth(), 20.9499), "half width includes convex radius");
    require(near(OpenOblivion::tes4BodyHalfHeight(), 64.6999), "half height includes convex radius");

    auto hull = OpenOblivion::makeTes4PlayerBody();
    require(hull->getNumPoints() == 18, "eight-sided prism with two apexes");
    require(near(hull->getMargin(), 0.69990, 1e-4), "convex radius becomes the margin");
    // Contact extents count the convex radius once. Bullet's cached broadphase
    // bounds add it a second time, which only enlarges culling bounds.
    const btVector3 east = hull->localGetSupportingVertex(btVector3(1, 0, 0));
    const btVector3 south = hull->localGetSupportingVertex(btVector3(0, -1, 0));
    const btVector3 apex = hull->localGetSupportingVertex(btVector3(0, 0, -1));
    const btVector3 top = hull->localGetSupportingVertex(btVector3(0, 0, 1));
    require(near(east.x(), OpenOblivion::tes4BodyHalfWidth()) && near(-south.y(), OpenOblivion::tes4BodyHalfWidth()),
        "support extents match reported half width");
    require(near(-apex.z(), OpenOblivion::tes4BodyHalfHeight()) && near(top.z(), OpenOblivion::tes4BodyHalfHeight()),
        "support extents match reported half height");
    btTransform identity;
    identity.setIdentity();
    btVector3 min, max;
    hull->getAabb(identity, min, max);
    require(max.x() >= east.x() && max.z() >= top.z() && min.z() <= apex.z(), "broadphase bounds contain the body");

    // The switch is explicit and exact.
    unsetenv("OPENOBLIVION_ORIGINAL_BODY");
    require(!OpenOblivion::tes4OriginalBodyEnabled(), "disabled by default");
    setenv("OPENOBLIVION_ORIGINAL_BODY", "true", 1);
    require(!OpenOblivion::tes4OriginalBodyEnabled(), "only 1 enables");
    setenv("OPENOBLIVION_ORIGINAL_BODY", "1", 1);
    require(OpenOblivion::tes4OriginalBodyEnabled(), "1 enables");

    World scene;
    btBoxShape floorShape(btVector3(500, 500, 10));
    btCollisionObject floor;
    floor.setCollisionShape(&floorShape);
    btTransform floorTransform;
    floorTransform.setIdentity();
    floorTransform.setOrigin(btVector3(0, 0, -10));
    floor.setWorldTransform(floorTransform);
    scene.world.addCollisionObject(&floor, MWPhysics::CollisionType_World, MWPhysics::CollisionType_Actor);

    btCollisionObject body;
    body.setCollisionShape(hull.get());
    btBoxShape boxShape(btVector3(13, 13, 69));
    btCollisionObject box;
    box.setCollisionShape(&boxShape);
    require(OpenOblivion::usesTes4Body(&body), "hull actor is recognised");
    require(!OpenOblivion::usesTes4Body(&box) && !OpenOblivion::usesTes4Body(nullptr), "other actors are not");

    const osg::Vec3f steep(0, -0.861f, 0.509f);
    const osg::Vec3f centre(0, 0, 66);
    const osg::Vec3f support = OpenOblivion::tes4SupportNormal(&body, &scene.world, centre, steep);
    require(near(support.z(), 1.0) && near(support.y(), 0.0), "cone edge contact uses the flat support below");
    const osg::Vec3f boxResult = OpenOblivion::tes4SupportNormal(&box, &scene.world, centre, steep);
    require(boxResult == steep, "box actors keep their contact normal");
    const osg::Vec3f far = OpenOblivion::tes4SupportNormal(&body, &scene.world, osg::Vec3f(0, 0, 200), steep);
    require(far == steep, "support beyond apex plus step reach keeps the contact normal");
    const osg::Vec3f outside = OpenOblivion::tes4SupportNormal(&body, &scene.world, osg::Vec3f(900, 0, 66), steep);
    require(outside == steep, "missing support keeps the contact normal");

    scene.world.removeCollisionObject(&floor);
    std::cout << "TES4 body fixtures passed: " << checks << " checks\n";
}
