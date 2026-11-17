// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/MotionPrimitiveSequence.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/motion_primitive_sequence.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__MOTION_PRIMITIVE_SEQUENCE__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__MOTION_PRIMITIVE_SEQUENCE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'motions'
#include "control_msgs/msg/detail/motion_primitive__struct.h"

/// Struct defined in msg/MotionPrimitiveSequence in the package control_msgs.
typedef struct control_msgs__msg__MotionPrimitiveSequence
{
  control_msgs__msg__MotionPrimitive__Sequence motions;
} control_msgs__msg__MotionPrimitiveSequence;

// Struct for a sequence of control_msgs__msg__MotionPrimitiveSequence.
typedef struct control_msgs__msg__MotionPrimitiveSequence__Sequence
{
  control_msgs__msg__MotionPrimitiveSequence * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__MotionPrimitiveSequence__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__MOTION_PRIMITIVE_SEQUENCE__STRUCT_H_
