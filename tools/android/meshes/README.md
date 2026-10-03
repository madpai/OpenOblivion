# Preview player collision model

`basicplayer.osgt` is an independently written serialization of the eight
collision-box corners in the pinned example-suite `BasicPlayer.dae`
(`id-mesh-2-positions-array`). X/Y are −13.3072..13.3072 and Z is
1.7012..140.0. The source and license audit is recorded in
[LICENSE_MATRIX.md](../../../docs/research/LICENSE_MATRIX.md).

OSGT's `#Generator` header requires two values. Additional `#` prose lines
after its headers are parsed as object data rather than skipped as comments.
Keep this explanation outside the model. An actual OSG reader regression
checks that the model loads, finds the Collision node and retains its triangles
and bounds. A failed load substitutes the engine's 123.203-unit-wide error
marker, which cannot pass the Vilverin frame's mid-height opening.

This is the existing preview template body, not a measured original Oblivion
character controller. Its dimensions and the movement/camera constants are
unchanged by the serialization fix.
