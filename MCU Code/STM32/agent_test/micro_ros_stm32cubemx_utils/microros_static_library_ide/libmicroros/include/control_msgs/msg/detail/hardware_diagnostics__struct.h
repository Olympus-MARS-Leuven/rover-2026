// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/HardwareDiagnostics.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/hardware_diagnostics.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__HARDWARE_DIAGNOSTICS__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__HARDWARE_DIAGNOSTICS__STRUCT_H_

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
// Member 'hardware_device_diagnostics'
#include "control_msgs/msg/detail/hardware_device_diagnostics__struct.h"

/// Struct defined in msg/HardwareDiagnostics in the package control_msgs.
/**
  * This message presents current hardware diagnostics
 */
typedef struct control_msgs__msg__HardwareDiagnostics
{
  /// Header timestamp should be update time of device diagnostics
  std_msgs__msg__Header header;
  /// Unique identifier per hardware component, ideally the name of the hardware derived from HardwareInfo e.g. "pal_arm"
  rosidl_runtime_c__String hardware_id;
  /// --- Device Diagnostics Aggregation ---------------------------------
  /// Diagnostics for individual devices within this hardware set
  control_msgs__msg__HardwareDeviceDiagnostics__Sequence hardware_device_diagnostics;
} control_msgs__msg__HardwareDiagnostics;

// Struct for a sequence of control_msgs__msg__HardwareDiagnostics.
typedef struct control_msgs__msg__HardwareDiagnostics__Sequence
{
  control_msgs__msg__HardwareDiagnostics * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__HardwareDiagnostics__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__HARDWARE_DIAGNOSTICS__STRUCT_H_
