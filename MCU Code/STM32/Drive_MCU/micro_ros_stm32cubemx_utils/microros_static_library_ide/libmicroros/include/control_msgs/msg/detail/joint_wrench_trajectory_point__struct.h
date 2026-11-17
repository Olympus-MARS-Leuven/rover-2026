// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/JointWrenchTrajectoryPoint.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/joint_wrench_trajectory_point.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__JOINT_WRENCH_TRAJECTORY_POINT__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__JOINT_WRENCH_TRAJECTORY_POINT__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'point'
#include "trajectory_msgs/msg/detail/joint_trajectory_point__struct.h"
// Member 'wrench'
#include "control_msgs/msg/detail/wrench_framed__struct.h"

/// Struct defined in msg/JointWrenchTrajectoryPoint in the package control_msgs.
/**
  * A joint-wrench trajectory point defines joint positions, joint velocities, joint accelerations, joint efforts, and a task space wrench, typically used by controllers.
  * Note: The time_from_start field is included in the JointTrajectoryPoint.
 */
typedef struct control_msgs__msg__JointWrenchTrajectoryPoint
{
  trajectory_msgs__msg__JointTrajectoryPoint point;
  /// The task-space wrench to apply at this trajectory point.
  control_msgs__msg__WrenchFramed wrench;
} control_msgs__msg__JointWrenchTrajectoryPoint;

// Struct for a sequence of control_msgs__msg__JointWrenchTrajectoryPoint.
typedef struct control_msgs__msg__JointWrenchTrajectoryPoint__Sequence
{
  control_msgs__msg__JointWrenchTrajectoryPoint * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__JointWrenchTrajectoryPoint__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__JOINT_WRENCH_TRAJECTORY_POINT__STRUCT_H_
