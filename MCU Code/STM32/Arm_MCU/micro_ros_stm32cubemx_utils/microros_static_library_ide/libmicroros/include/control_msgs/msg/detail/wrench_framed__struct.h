// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/WrenchFramed.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/wrench_framed.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__WRENCH_FRAMED__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__WRENCH_FRAMED__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'frame_id'
#include "rosidl_runtime_c/string.h"
// Member 'wrench'
#include "geometry_msgs/msg/detail/wrench__struct.h"

/// Struct defined in msg/WrenchFramed in the package control_msgs.
/**
  * This message represents a wrench (force and torque) expressed in a specific reference frame.
 */
typedef struct control_msgs__msg__WrenchFramed
{
  /// The reference frame in which the wrench is expressed.
  rosidl_runtime_c__String frame_id;
  /// The wrench applied.
  geometry_msgs__msg__Wrench wrench;
} control_msgs__msg__WrenchFramed;

// Struct for a sequence of control_msgs__msg__WrenchFramed.
typedef struct control_msgs__msg__WrenchFramed__Sequence
{
  control_msgs__msg__WrenchFramed * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__WrenchFramed__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__WRENCH_FRAMED__STRUCT_H_
