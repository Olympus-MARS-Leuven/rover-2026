// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/JointWrenchTrajectory.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/joint_wrench_trajectory.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__JOINT_WRENCH_TRAJECTORY__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__JOINT_WRENCH_TRAJECTORY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'joint_names'
#include "rosidl_runtime_c/string.h"
// Member 'points'
#include "control_msgs/msg/detail/joint_wrench_trajectory_point__struct.h"

/// Struct defined in msg/JointWrenchTrajectory in the package control_msgs.
/**
  * The header is used to specify the reference time for the trajectory durations
 */
typedef struct control_msgs__msg__JointWrenchTrajectory
{
  std_msgs__msg__Header header;
  /// The names of the active joints in each trajectory point. These names are
  /// ordered and must correspond to the values in each trajectory point.
  rosidl_runtime_c__String__Sequence joint_names;
  /// Array of trajectory points, which describe the joint positions, velocities,
  /// accelerations and/or efforts, and task space wrenches at each time point.
  control_msgs__msg__JointWrenchTrajectoryPoint__Sequence points;
} control_msgs__msg__JointWrenchTrajectory;

// Struct for a sequence of control_msgs__msg__JointWrenchTrajectory.
typedef struct control_msgs__msg__JointWrenchTrajectory__Sequence
{
  control_msgs__msg__JointWrenchTrajectory * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__JointWrenchTrajectory__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__JOINT_WRENCH_TRAJECTORY__STRUCT_H_
