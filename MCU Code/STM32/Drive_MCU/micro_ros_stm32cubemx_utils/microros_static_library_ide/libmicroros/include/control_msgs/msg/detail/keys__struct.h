// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/Keys.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/keys.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__KEYS__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__KEYS__STRUCT_H_

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
// Member 'keys'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/Keys in the package control_msgs.
typedef struct control_msgs__msg__Keys
{
  std_msgs__msg__Header header;
  /// List of names defining interfaces or joints or other string-based entities
  /// being published with Keys.msg
  rosidl_runtime_c__String__Sequence keys;
} control_msgs__msg__Keys;

// Struct for a sequence of control_msgs__msg__Keys.
typedef struct control_msgs__msg__Keys__Sequence
{
  control_msgs__msg__Keys * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__Keys__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__KEYS__STRUCT_H_
