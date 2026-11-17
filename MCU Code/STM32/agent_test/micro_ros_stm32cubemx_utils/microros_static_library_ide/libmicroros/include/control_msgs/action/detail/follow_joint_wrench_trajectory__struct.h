// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from control_msgs:action/FollowJointWrenchTrajectory.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/action/follow_joint_wrench_trajectory.h"


#ifndef CONTROL_MSGS__ACTION__DETAIL__FOLLOW_JOINT_WRENCH_TRAJECTORY__STRUCT_H_
#define CONTROL_MSGS__ACTION__DETAIL__FOLLOW_JOINT_WRENCH_TRAJECTORY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'trajectory'
#include "control_msgs/msg/detail/joint_wrench_trajectory__struct.h"
// Member 'path_tolerance'
// Member 'goal_tolerance'
#include "control_msgs/msg/detail/joint_tolerance__struct.h"
// Member 'goal_time_tolerance'
#include "builtin_interfaces/msg/detail/duration__struct.h"

/// Struct defined in action/FollowJointWrenchTrajectory in the package control_msgs.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_Goal
{
  control_msgs__msg__JointWrenchTrajectory trajectory;
  /// Tolerances for the trajectory.  If the measured joint values fall
  /// outside the tolerances the trajectory goal is aborted.  Any
  /// tolerances that are not specified (by being omitted or set to 0) are
  /// set to the defaults for the action server (often taken from the
  /// parameter server).
  /// Tolerances applied to the joints as the trajectory is executed.  If
  /// violated, the goal aborts with error_code set to
  /// PATH_TOLERANCE_VIOLATED.
  control_msgs__msg__JointTolerance__Sequence path_tolerance;
  /// To report success, the joints must be within goal_tolerance of the
  /// final trajectory value.  The goal must be achieved by time the
  /// trajectory ends plus goal_time_tolerance.  (goal_time_tolerance
  /// allows some leeway in time, so that the trajectory goal can still
  /// succeed even if the joints reach the goal some time after the
  /// precise end time of the trajectory).
  ///
  /// If the joints are not within goal_tolerance after "trajectory finish
  /// time" + goal_time_tolerance, the goal aborts with error_code set to
  /// GOAL_TOLERANCE_VIOLATED
  control_msgs__msg__JointTolerance__Sequence goal_tolerance;
  builtin_interfaces__msg__Duration goal_time_tolerance;
} control_msgs__action__FollowJointWrenchTrajectory_Goal;

// Struct for a sequence of control_msgs__action__FollowJointWrenchTrajectory_Goal.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_Goal__Sequence
{
  control_msgs__action__FollowJointWrenchTrajectory_Goal * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__action__FollowJointWrenchTrajectory_Goal__Sequence;

// Constants defined in the message

/// Constant 'SUCCESSFUL'.
enum
{
  control_msgs__action__FollowJointWrenchTrajectory_Result__SUCCESSFUL = 0l
};

/// Constant 'INVALID_GOAL'.
enum
{
  control_msgs__action__FollowJointWrenchTrajectory_Result__INVALID_GOAL = -1l
};

/// Constant 'INVALID_JOINTS'.
enum
{
  control_msgs__action__FollowJointWrenchTrajectory_Result__INVALID_JOINTS = -2l
};

/// Constant 'OLD_HEADER_TIMESTAMP'.
enum
{
  control_msgs__action__FollowJointWrenchTrajectory_Result__OLD_HEADER_TIMESTAMP = -3l
};

/// Constant 'PATH_TOLERANCE_VIOLATED'.
enum
{
  control_msgs__action__FollowJointWrenchTrajectory_Result__PATH_TOLERANCE_VIOLATED = -4l
};

/// Constant 'GOAL_TOLERANCE_VIOLATED'.
enum
{
  control_msgs__action__FollowJointWrenchTrajectory_Result__GOAL_TOLERANCE_VIOLATED = -5l
};

/// Constant 'TRAJECTORY_ABORTED'.
enum
{
  control_msgs__action__FollowJointWrenchTrajectory_Result__TRAJECTORY_ABORTED = -6l
};

// Include directives for member types
// Member 'error_string'
#include "rosidl_runtime_c/string.h"

/// Struct defined in action/FollowJointWrenchTrajectory in the package control_msgs.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_Result
{
  int32_t error_code;
  /// Human readable description of the error code. Contains complementary
  /// information that is especially useful when execution fails, for instance:
  /// - INVALID_GOAL: The reason for the invalid goal (e.g., the requested
  ///   trajectory requires a command that differ significantly from the
  ///   robot's current state).
  /// - INVALID_JOINTS: The mismatch between the expected controller joints
  ///   and those provided in the goal.
  /// - PATH_TOLERANCE_VIOLATED and GOAL_TOLERANCE_VIOLATED: Which joint
  ///   violated which tolerance, and by how much.
  /// - TRAJECTORY_ABORTED: Indicates that the trajectory was aborted during
  ///   execution (e.g., another trajectory was sent for execution, or a
  ///   problem occurred).
  rosidl_runtime_c__String error_string;
} control_msgs__action__FollowJointWrenchTrajectory_Result;

// Struct for a sequence of control_msgs__action__FollowJointWrenchTrajectory_Result.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_Result__Sequence
{
  control_msgs__action__FollowJointWrenchTrajectory_Result * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__action__FollowJointWrenchTrajectory_Result__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'joint_names'
// already included above
// #include "rosidl_runtime_c/string.h"
// Member 'desired'
// Member 'actual'
// Member 'error'
#include "control_msgs/msg/detail/joint_wrench_trajectory_point__struct.h"

/// Struct defined in action/FollowJointWrenchTrajectory in the package control_msgs.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_Feedback
{
  std_msgs__msg__Header header;
  rosidl_runtime_c__String__Sequence joint_names;
  control_msgs__msg__JointWrenchTrajectoryPoint desired;
  control_msgs__msg__JointWrenchTrajectoryPoint actual;
  control_msgs__msg__JointWrenchTrajectoryPoint error;
  /// the currently used point from trajectory.points array
  int32_t index;
} control_msgs__action__FollowJointWrenchTrajectory_Feedback;

// Struct for a sequence of control_msgs__action__FollowJointWrenchTrajectory_Feedback.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_Feedback__Sequence
{
  control_msgs__action__FollowJointWrenchTrajectory_Feedback * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__action__FollowJointWrenchTrajectory_Feedback__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
#include "unique_identifier_msgs/msg/detail/uuid__struct.h"
// Member 'goal'
#include "control_msgs/action/detail/follow_joint_wrench_trajectory__struct.h"

/// Struct defined in action/FollowJointWrenchTrajectory in the package control_msgs.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Request
{
  unique_identifier_msgs__msg__UUID goal_id;
  control_msgs__action__FollowJointWrenchTrajectory_Goal goal;
} control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Request;

// Struct for a sequence of control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Request.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Request__Sequence
{
  control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__struct.h"

/// Struct defined in action/FollowJointWrenchTrajectory in the package control_msgs.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Response
{
  bool accepted;
  builtin_interfaces__msg__Time stamp;
} control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Response;

// Struct for a sequence of control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Response.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Response__Sequence
{
  control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Event__request__MAX_SIZE = 1
};
// response
enum
{
  control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Event__response__MAX_SIZE = 1
};

/// Struct defined in action/FollowJointWrenchTrajectory in the package control_msgs.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Event
{
  service_msgs__msg__ServiceEventInfo info;
  control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Request__Sequence request;
  control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Response__Sequence response;
} control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Event;

// Struct for a sequence of control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Event.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Event__Sequence
{
  control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__action__FollowJointWrenchTrajectory_SendGoal_Event__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.h"

/// Struct defined in action/FollowJointWrenchTrajectory in the package control_msgs.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_GetResult_Request
{
  unique_identifier_msgs__msg__UUID goal_id;
} control_msgs__action__FollowJointWrenchTrajectory_GetResult_Request;

// Struct for a sequence of control_msgs__action__FollowJointWrenchTrajectory_GetResult_Request.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_GetResult_Request__Sequence
{
  control_msgs__action__FollowJointWrenchTrajectory_GetResult_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__action__FollowJointWrenchTrajectory_GetResult_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'result'
// already included above
// #include "control_msgs/action/detail/follow_joint_wrench_trajectory__struct.h"

/// Struct defined in action/FollowJointWrenchTrajectory in the package control_msgs.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_GetResult_Response
{
  int8_t status;
  control_msgs__action__FollowJointWrenchTrajectory_Result result;
} control_msgs__action__FollowJointWrenchTrajectory_GetResult_Response;

// Struct for a sequence of control_msgs__action__FollowJointWrenchTrajectory_GetResult_Response.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_GetResult_Response__Sequence
{
  control_msgs__action__FollowJointWrenchTrajectory_GetResult_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__action__FollowJointWrenchTrajectory_GetResult_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
// already included above
// #include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  control_msgs__action__FollowJointWrenchTrajectory_GetResult_Event__request__MAX_SIZE = 1
};
// response
enum
{
  control_msgs__action__FollowJointWrenchTrajectory_GetResult_Event__response__MAX_SIZE = 1
};

/// Struct defined in action/FollowJointWrenchTrajectory in the package control_msgs.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_GetResult_Event
{
  service_msgs__msg__ServiceEventInfo info;
  control_msgs__action__FollowJointWrenchTrajectory_GetResult_Request__Sequence request;
  control_msgs__action__FollowJointWrenchTrajectory_GetResult_Response__Sequence response;
} control_msgs__action__FollowJointWrenchTrajectory_GetResult_Event;

// Struct for a sequence of control_msgs__action__FollowJointWrenchTrajectory_GetResult_Event.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_GetResult_Event__Sequence
{
  control_msgs__action__FollowJointWrenchTrajectory_GetResult_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__action__FollowJointWrenchTrajectory_GetResult_Event__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.h"
// Member 'feedback'
// already included above
// #include "control_msgs/action/detail/follow_joint_wrench_trajectory__struct.h"

/// Struct defined in action/FollowJointWrenchTrajectory in the package control_msgs.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_FeedbackMessage
{
  unique_identifier_msgs__msg__UUID goal_id;
  control_msgs__action__FollowJointWrenchTrajectory_Feedback feedback;
} control_msgs__action__FollowJointWrenchTrajectory_FeedbackMessage;

// Struct for a sequence of control_msgs__action__FollowJointWrenchTrajectory_FeedbackMessage.
typedef struct control_msgs__action__FollowJointWrenchTrajectory_FeedbackMessage__Sequence
{
  control_msgs__action__FollowJointWrenchTrajectory_FeedbackMessage * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} control_msgs__action__FollowJointWrenchTrajectory_FeedbackMessage__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__ACTION__DETAIL__FOLLOW_JOINT_WRENCH_TRAJECTORY__STRUCT_H_
