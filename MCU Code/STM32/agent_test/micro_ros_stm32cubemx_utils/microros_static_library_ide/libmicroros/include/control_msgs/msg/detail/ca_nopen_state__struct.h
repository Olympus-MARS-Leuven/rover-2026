// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:msg/CANopenState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/ca_nopen_state.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__CA_NOPEN_STATE__STRUCT_H_
#define CONTROL_MSGS__MSG__DETAIL__CA_NOPEN_STATE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

/// Constant 'NMT_INITIALISING'.
/**
  * --- NMT State Constants -------------------------------------------
  * CiA 301 Network Management states
  * Device is initializing
 */
enum
{
  control_msgs__msg__CANopenState__NMT_INITIALISING = 0
};

/// Constant 'NMT_PRE_OPERATIONAL'.
/**
  * Device is in pre-operational state
 */
enum
{
  control_msgs__msg__CANopenState__NMT_PRE_OPERATIONAL = 127
};

/// Constant 'NMT_OPERATIONAL'.
/**
  * Device is operational
 */
enum
{
  control_msgs__msg__CANopenState__NMT_OPERATIONAL = 5
};

/// Constant 'NMT_STOPPED'.
/**
  * Device is stopped
 */
enum
{
  control_msgs__msg__CANopenState__NMT_STOPPED = 4
};

/// Constant 'DSP402_NOT_READY_TO_SWITCH_ON'.
/**
  * --- DSP 402 State Constants ---------------------------------------
  * CiA 402 Drive state machine states
  * Not ready to switch on
 */
enum
{
  control_msgs__msg__CANopenState__DSP402_NOT_READY_TO_SWITCH_ON = 0
};

/// Constant 'DSP402_SWITCH_ON_DISABLED'.
/**
  * Switch on disabled
 */
enum
{
  control_msgs__msg__CANopenState__DSP402_SWITCH_ON_DISABLED = 1
};

/// Constant 'DSP402_READY_TO_SWITCH_ON'.
/**
  * Ready to switch on
 */
enum
{
  control_msgs__msg__CANopenState__DSP402_READY_TO_SWITCH_ON = 2
};

/// Constant 'DSP402_SWITCHED_ON'.
/**
  * Switched on
 */
enum
{
  control_msgs__msg__CANopenState__DSP402_SWITCHED_ON = 3
};

/// Constant 'DSP402_OPERATION_ENABLED'.
/**
  * Operation enabled
 */
enum
{
  control_msgs__msg__CANopenState__DSP402_OPERATION_ENABLED = 4
};

/// Constant 'DSP402_QUICK_STOP_ACTIVE'.
/**
  * Quick stop active
 */
enum
{
  control_msgs__msg__CANopenState__DSP402_QUICK_STOP_ACTIVE = 5
};

/// Constant 'DSP402_FAULT_REACTION_ACTIVE'.
/**
  * Fault reaction active
 */
enum
{
  control_msgs__msg__CANopenState__DSP402_FAULT_REACTION_ACTIVE = 6
};

/// Constant 'DSP402_FAULT'.
/**
  * Fault state
 */
enum
{
  control_msgs__msg__CANopenState__DSP402_FAULT = 7
};

/// Struct defined in msg/CANopenState in the package control_msgs.
/**
  * This message presents CANopen-specific device state information
  * Refer CiA 301 and CiA 402 application layer documentation
 */
typedef struct control_msgs__msg__CANopenState
{
  /// The CANopen node ID of the device (1-127)
  uint8_t node_id;
  /// --- CiA 301 State -------------------------------------------------
  /// Network Management state, see NMTState constants below
  uint8_t nmt_state;
  /// --- CiA 402 State (for drives) ------------------------------------
  /// Drive state machine state for motion control devices, see DSP402State constants below
  uint8_t dsp_402_state;
  /// --- Error Reporting -----------------------------------------------
  /// Last Emergency (EMCY) error code received from the device
  uint32_t last_emcy_code;
} control_msgs__msg__CANopenState;

// Struct for a sequence of control_msgs__msg__CANopenState.
typedef struct control_msgs__msg__CANopenState__Sequence
{
  control_msgs__msg__CANopenState * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__msg__CANopenState__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__CA_NOPEN_STATE__STRUCT_H_
