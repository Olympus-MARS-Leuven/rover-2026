// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/BatteryStateArray.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/battery_state_array.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__BATTERY_STATE_ARRAY__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__BATTERY_STATE_ARRAY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'battery_states'
#include "sensor_msgs/msg/detail/battery_state__struct.h"

/// Struct defined in msg/BatteryStateArray in the package control_msgs.
/**
  * This message publishes values for multiple batteries at once.
 */
typedef struct control_msgs__msg__BatteryStateArray
{
  sensor_msgs__msg__BatteryState__Sequence battery_states;
} control_msgs__msg__BatteryStateArray;

// Struct for a sequence of control_msgs__msg__BatteryStateArray.
typedef struct control_msgs__msg__BatteryStateArray__Sequence
{
  control_msgs__msg__BatteryStateArray * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__BatteryStateArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__BATTERY_STATE_ARRAY__STRUCT_H_
