// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/MotionArgument.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/motion_argument.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__MOTION_ARGUMENT__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__MOTION_ARGUMENT__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'name'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/MotionArgument in the package control_msgs.
/**
  * Key Value pair to be used in MotionPrimitive messages
 */
typedef struct control_msgs__msg__MotionArgument
{
  rosidl_runtime_c__String name;
  double value;
} control_msgs__msg__MotionArgument;

// Struct for a sequence of control_msgs__msg__MotionArgument.
typedef struct control_msgs__msg__MotionArgument__Sequence
{
  control_msgs__msg__MotionArgument * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__MotionArgument__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__MOTION_ARGUMENT__STRUCT_H_
