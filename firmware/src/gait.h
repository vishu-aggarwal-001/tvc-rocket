#pragma once
// Walking: a wave gait for 2-DOF legs (hip yaw + knee). Each leg spends `duty` of the
// cycle on the ground sweeping backwards (that pushes the body along) and the rest
// lifted, swinging forwards. Creep (duty 0.75, one leg up at a time) is the steady
// default; trot (duty 0.5, diagonal pairs) is faster.
namespace Gait {
enum Kind { CREEP, TROT };
void setKind(Kind k);
Kind kind();
// fwd, turn in -1..1 (turn > 0 = turn left); height in -1..1 (crouch .. tall)
void update(float dt, float fwd, float turn, float height);
void stand(float height = 0);
}
