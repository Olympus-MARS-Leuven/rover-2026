// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/EtherCATState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/ether_cat_state.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__ETHER_CAT_STATE__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__ETHER_CAT_STATE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

/// Constant 'AL_STATE_INIT'.
/**
  * --- Application Layer State Constants -----------------------------
  * EtherCAT slave states according to ETG.1000
  * INIT state - slave initialization
 */
enum
{
  control_msgs__msg__EtherCATState__AL_STATE_INIT = 1
};

/// Constant 'AL_STATE_PREOP'.
/**
  * PREOP state - pre-operational, mailbox communication
 */
enum
{
  control_msgs__msg__EtherCATState__AL_STATE_PREOP = 2
};

/// Constant 'AL_STATE_BOOTSTRAP'.
/**
  * BOOTSTRAP state - firmware update mode
 */
enum
{
  control_msgs__msg__EtherCATState__AL_STATE_BOOTSTRAP = 3
};

/// Constant 'AL_STATE_SAFEOP'.
/**
  * SAFEOP state - safe operational, inputs updated
 */
enum
{
  control_msgs__msg__EtherCATState__AL_STATE_SAFEOP = 4
};

/// Constant 'AL_STATE_OP'.
/**
  * OP state - operational, full communication
 */
enum
{
  control_msgs__msg__EtherCATState__AL_STATE_OP = 8
};

// Include directives for member types
// Member 'vendor_id'
// Member 'product_code'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/EtherCATState in the package control_msgs.
/**
  * This message presents EtherCAT-specific device state information
  * Refer ETG.1000 EtherCAT Specification
 */
typedef struct control_msgs__msg__EtherCATState
{
  /// Position of the slave on the bus (0, 1, 2...)
  uint16_t slave_position;
  /// Unique vendor identifier from the device's ESI file
  rosidl_runtime_c__String vendor_id;
  /// Unique product code for the device from the device's ESI file
  rosidl_runtime_c__String product_code;
  /// --- EtherCAT State Machine (ESM) ----------------------------------
  /// Application Layer state, see ALState constants below
  uint8_t al_state;
  /// True if the slave is in an error state
  bool has_error;
  /// AL Status Code indicating the reason for an error (0 = no error)
  uint16_t al_status_code;
} control_msgs__msg__EtherCATState;

// Struct for a sequence of control_msgs__msg__EtherCATState.
typedef struct control_msgs__msg__EtherCATState__Sequence
{
  control_msgs__msg__EtherCATState * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__EtherCATState__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__ETHER_CAT_STATE__STRUCT_H_
