// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/HardwareDeviceDiagnostics.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/hardware_device_diagnostics.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__HARDWARE_DEVICE_DIAGNOSTICS__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__HARDWARE_DEVICE_DIAGNOSTICS__STRUCT_H_

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
// Member 'device_id'
#include "rosidl_runtime_c/string.h"
// Member 'entries'
#include "diagnostic_msgs/msg/detail/key_value__struct.h"

/// Struct defined in msg/HardwareDeviceDiagnostics in the package control_msgs.
/**
  * This message presents current hardware device status information
 */
typedef struct control_msgs__msg__HardwareDeviceDiagnostics
{
  /// Header timestamp should be update time of device diagnostics
  std_msgs__msg__Header header;
  /// Unique identifier for the device, e.g. "base_motor", "gripper_joint_1"
  rosidl_runtime_c__String device_id;
  /// --- Diagnostic Entries --------------------------------------------
  /// Key-value pairs representing diagnostic information for the device.
  diagnostic_msgs__msg__KeyValue__Sequence entries;
} control_msgs__msg__HardwareDeviceDiagnostics;

// Struct for a sequence of control_msgs__msg__HardwareDeviceDiagnostics.
typedef struct control_msgs__msg__HardwareDeviceDiagnostics__Sequence
{
  control_msgs__msg__HardwareDeviceDiagnostics * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__HardwareDeviceDiagnostics__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__HARDWARE_DEVICE_DIAGNOSTICS__STRUCT_H_
