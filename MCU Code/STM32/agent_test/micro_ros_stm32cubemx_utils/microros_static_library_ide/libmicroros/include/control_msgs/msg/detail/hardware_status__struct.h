// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/HardwareStatus.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/hardware_status.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__HARDWARE_STATUS__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__HARDWARE_STATUS__STRUCT_H_

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
// Member 'hardware_id'
#include "rosidl_runtime_c/string.h"
// Member 'hardware_device_states'
#include "control_msgs/msg/detail/hardware_device_status__struct.h"

/// Struct defined in msg/HardwareStatus in the package control_msgs.
/**
  * This message presents current hardware component status information
 */
typedef struct control_msgs__msg__HardwareStatus
{
  /// Header timestamp should be update time of hardware status
  std_msgs__msg__Header header;
  /// Unique identifier per hardware component, ideally the name of the hardware derived from HardwareInfo e.g. "pal_arm"
  rosidl_runtime_c__String hardware_id;
  /// --- Device Status Aggregation ---------------------------------
  /// An array containing the status of individual devices in the hardware component
  control_msgs__msg__HardwareDeviceStatus__Sequence hardware_device_states;
} control_msgs__msg__HardwareStatus;

// Struct for a sequence of control_msgs__msg__HardwareStatus.
typedef struct control_msgs__msg__HardwareStatus__Sequence
{
  control_msgs__msg__HardwareStatus * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__HardwareStatus__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__HARDWARE_STATUS__STRUCT_H_
