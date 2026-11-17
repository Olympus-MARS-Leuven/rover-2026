// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/HardwareDeviceStatus.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/hardware_device_status.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__HARDWARE_DEVICE_STATUS__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__HARDWARE_DEVICE_STATUS__STRUCT_H_

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
// Member 'hardware_status'
#include "control_msgs/msg/detail/generic_hardware_state__struct.h"
// Member 'canopen_states'
#include "control_msgs/msg/detail/ca_nopen_state__struct.h"
// Member 'ethercat_states'
#include "control_msgs/msg/detail/ether_cat_state__struct.h"
// Member 'vda5050_states'
#include "control_msgs/msg/detail/vda5050_state__struct.h"

/// Struct defined in msg/HardwareDeviceStatus in the package control_msgs.
/**
  * This message presents current hardware device status information
 */
typedef struct control_msgs__msg__HardwareDeviceStatus
{
  /// Header timestamp should be update time of device status
  std_msgs__msg__Header header;
  /// Unique identifier for the device, e.g. "base_motor", "gripper_joint_1"
  rosidl_runtime_c__String device_id;
  /// --- Standard-Specific States --------------------------------------
  /// States populated based on the standards relevant to this device.
  /// A device will only fill the arrays for the standards it implements, rest will be empty
  /// Generic hardware status information applicable to any device, it is suggested to fill this for all devices
  control_msgs__msg__GenericHardwareState__Sequence hardware_status;
  /// CANopen-specific device states (DS-301/DS-402 compliant devices)
  control_msgs__msg__CANopenState__Sequence canopen_states;
  /// EtherCAT-specific device states (CoE, FoE, etc.)
  control_msgs__msg__EtherCATState__Sequence ethercat_states;
  /// VDA5050-specific states for AGV/mobile robot devices
  control_msgs__msg__VDA5050State__Sequence vda5050_states;
} control_msgs__msg__HardwareDeviceStatus;

// Struct for a sequence of control_msgs__msg__HardwareDeviceStatus.
typedef struct control_msgs__msg__HardwareDeviceStatus__Sequence
{
  control_msgs__msg__HardwareDeviceStatus * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__HardwareDeviceStatus__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__HARDWARE_DEVICE_STATUS__STRUCT_H_
