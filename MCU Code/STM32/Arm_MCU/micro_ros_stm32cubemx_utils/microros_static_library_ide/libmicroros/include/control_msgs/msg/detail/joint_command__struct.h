// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/JointCommand.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/joint_command.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__JOINT_COMMAND__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__JOINT_COMMAND__STRUCT_H_

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
// Member 'interface_name'
#include "rosidl_runtime_c/string.h"
// Member 'values'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in msg/JointCommand in the package control_msgs.
/**
  * This message contains the command for a specific interface across multiple joints.
 */
typedef struct control_msgs__msg__JointCommand
{
  std_msgs__msg__Header header;
  /// List of joint names to command.
  rosidl_runtime_c__String__Sequence joint_names;
  /// The specific interface type to command (e.g., "position", "velocity", "effort").
  rosidl_runtime_c__String interface_name;
  /// The commanded values. The length of this array must exactly match the length of joint_names.
  rosidl_runtime_c__double__Sequence values;
} control_msgs__msg__JointCommand;

// Struct for a sequence of control_msgs__msg__JointCommand.
typedef struct control_msgs__msg__JointCommand__Sequence
{
  control_msgs__msg__JointCommand * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__JointCommand__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__JOINT_COMMAND__STRUCT_H_
