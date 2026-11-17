// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:srv/SetOdometry.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/srv/set_odometry.h"


#ifndef CONTROL_MSGS__SRV__DETAIL__SET_ODOMETRY__STRUCT_H_
#define CONTROL_MSGS__SRV__DETAIL__SET_ODOMETRY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in srv/SetOdometry in the package control_msgs.
typedef struct control_msgs__srv__SetOdometry_Request
{
  double x;
  double y;
  double z;
  double roll;
  double pitch;
  double yaw;
} control_msgs__srv__SetOdometry_Request;

// Struct for a sequence of control_msgs__srv__SetOdometry_Request.
typedef struct control_msgs__srv__SetOdometry_Request__Sequence
{
  control_msgs__srv__SetOdometry_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__srv__SetOdometry_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'message'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/SetOdometry in the package control_msgs.
typedef struct control_msgs__srv__SetOdometry_Response
{
  bool success;
  rosidl_runtime_c__String message;
} control_msgs__srv__SetOdometry_Response;

// Struct for a sequence of control_msgs__srv__SetOdometry_Response.
typedef struct control_msgs__srv__SetOdometry_Response__Sequence
{
  control_msgs__srv__SetOdometry_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__srv__SetOdometry_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  control_msgs__srv__SetOdometry_Event__request__MAX_SIZE = 1
};
// response
enum
{
  control_msgs__srv__SetOdometry_Event__response__MAX_SIZE = 1
};

/// Struct defined in srv/SetOdometry in the package control_msgs.
typedef struct control_msgs__srv__SetOdometry_Event
{
  service_msgs__msg__ServiceEventInfo info;
  control_msgs__srv__SetOdometry_Request__Sequence request;
  control_msgs__srv__SetOdometry_Response__Sequence response;
} control_msgs__srv__SetOdometry_Event;

// Struct for a sequence of control_msgs__srv__SetOdometry_Event.
typedef struct control_msgs__srv__SetOdometry_Event__Sequence
{
  control_msgs__srv__SetOdometry_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__srv__SetOdometry_Event__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__SRV__DETAIL__SET_ODOMETRY__STRUCT_H_
