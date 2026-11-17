// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/MotionPrimitive.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/motion_primitive.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__MOTION_PRIMITIVE__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__MOTION_PRIMITIVE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

/// Constant 'UNKNOWN'.
enum
{
  control_msgs__msg__MotionPrimitive__UNKNOWN = -1
};

/// Constant 'LINEAR_JOINT'.
/**
  * Often referred as PTP
 */
enum
{
  control_msgs__msg__MotionPrimitive__LINEAR_JOINT = 0
};

/// Constant 'LINEAR_CARTESIAN'.
/**
  * Often referred as LIN
 */
enum
{
  control_msgs__msg__MotionPrimitive__LINEAR_CARTESIAN = 50
};

/// Constant 'CIRCULAR_CARTESIAN'.
/**
  * Often referred as CIRC
 */
enum
{
  control_msgs__msg__MotionPrimitive__CIRCULAR_CARTESIAN = 51
};

// Include directives for member types
// Member 'additional_arguments'
#include "control_msgs/msg/detail/motion_argument__struct.h"
// Member 'poses'
#include "geometry_msgs/msg/detail/pose_stamped__struct.h"
// Member 'joint_positions'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in msg/MotionPrimitive in the package control_msgs.
typedef struct control_msgs__msg__MotionPrimitive
{
  /// potentially more, such as spline motion
  /// one of the above
  int8_t type;
  double blend_radius;
  /// MotionArguments are meant to be used as vendor-specific or use-case-specific arguments to
  /// MotionPrimitive messages. This is to avoid bloating the MotionPrimitive message with all possible
  /// uses cases but rather add specific data using as a list of key-value pairs, which is what this
  /// message represents.
  /// (max) velocity, (max) acceleration, efficiency
  control_msgs__msg__MotionArgument__Sequence additional_arguments;
  /// Targets should be either specified through joint configurations or Cartesian poses.
  /// Depending on the motion type and implementation, there might be multiple poses allowed.
  /// For example, circular motions are often specified as via and target
  /// Usually one of these is empty, in some edge cases even both can be empty, when all input is given
  /// in the more flexible MotionArgument[] field.
  geometry_msgs__msg__PoseStamped__Sequence poses;
  rosidl_runtime_c__double__Sequence joint_positions;
} control_msgs__msg__MotionPrimitive;

// Struct for a sequence of control_msgs__msg__MotionPrimitive.
typedef struct control_msgs__msg__MotionPrimitive__Sequence
{
  control_msgs__msg__MotionPrimitive * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__MotionPrimitive__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__MOTION_PRIMITIVE__STRUCT_H_
