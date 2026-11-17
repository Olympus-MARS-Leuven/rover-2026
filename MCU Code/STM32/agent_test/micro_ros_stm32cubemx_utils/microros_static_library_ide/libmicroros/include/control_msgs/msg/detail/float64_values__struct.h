// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/Float64Values.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/float64_values.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__FLOAT64_VALUES__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__FLOAT64_VALUES__STRUCT_H_

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
// Member 'values'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in msg/Float64Values in the package control_msgs.
typedef struct control_msgs__msg__Float64Values
{
  std_msgs__msg__Header header;
  /// List of values corresponding to the interfaces or joints defined in Keys.msg
  /// The size and order must match that of Keys.msg
  /// Each value corresponds to the key at the same index in Keys.msg
  ///
  /// For example. if Keys.msg has keys = ["joint1/position", "joint2/velocity"], then
  /// InterfacesValues.msg could have values = [1.57, 0.0]. The first value (1.57) corresponds to "joint1/position"
  /// and the second value (0.0) corresponds to "joint2/velocity"
  ///
  /// This message is used by the interfaces_state_broadcaster to publish the values of the interfaces via
  /// ROS 2 topics ~/names (Keys.msg) and ~/values (InterfacesValues.msg)
  rosidl_runtime_c__double__Sequence values;
} control_msgs__msg__Float64Values;

// Struct for a sequence of control_msgs__msg__Float64Values.
typedef struct control_msgs__msg__Float64Values__Sequence
{
  control_msgs__msg__Float64Values * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__Float64Values__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__FLOAT64_VALUES__STRUCT_H_
