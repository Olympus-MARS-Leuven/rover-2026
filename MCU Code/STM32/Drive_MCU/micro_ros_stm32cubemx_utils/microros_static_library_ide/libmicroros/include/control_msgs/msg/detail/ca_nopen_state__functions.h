// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from control_msgs:msg/CANopenState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "control_msgs/msg/ca_nopen_state.h"


#ifndef CONTROL_MSGS__MSG__DETAIL__CA_NOPEN_STATE__FUNCTIONS_H_
#define CONTROL_MSGS__MSG__DETAIL__CA_NOPEN_STATE__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/action_type_support_struct.h"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_runtime_c/service_type_support_struct.h"
#include "rosidl_runtime_c/type_description/type_description__struct.h"
#include "rosidl_runtime_c/type_description/type_source__struct.h"
#include "rosidl_runtime_c/type_hash.h"
#include "rosidl_runtime_c/visibility_control.h"
#include "control_msgs/msg/rosidl_generator_c__visibility_control.h"

#include "control_msgs/msg/detail/ca_nopen_state__struct.h"

/// Initialize msg/CANopenState message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * control_msgs__msg__CANopenState
 * )) before or use
 * control_msgs__msg__CANopenState__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_control_msgs
bool
control_msgs__msg__CANopenState__init(control_msgs__msg__CANopenState * msg);

/// Finalize msg/CANopenState message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_control_msgs
void
control_msgs__msg__CANopenState__fini(control_msgs__msg__CANopenState * msg);

/// Create msg/CANopenState message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * control_msgs__msg__CANopenState__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_control_msgs
control_msgs__msg__CANopenState *
control_msgs__msg__CANopenState__create(void);

/// Destroy msg/CANopenState message.
/**
 * It calls
 * control_msgs__msg__CANopenState__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_control_msgs
void
control_msgs__msg__CANopenState__destroy(control_msgs__msg__CANopenState * msg);

/// Check for msg/CANopenState message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_control_msgs
bool
control_msgs__msg__CANopenState__are_equal(const control_msgs__msg__CANopenState * lhs, const control_msgs__msg__CANopenState * rhs);

/// Copy a msg/CANopenState message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_control_msgs
bool
control_msgs__msg__CANopenState__copy(
  const control_msgs__msg__CANopenState * input,
  control_msgs__msg__CANopenState * output);

/// Retrieve pointer to the hash of the description of this type.
ROSIDL_GENERATOR_C_PUBLIC_control_msgs
const rosidl_type_hash_t *
control_msgs__msg__CANopenState__get_type_hash(
  const rosidl_message_type_support_t * type_support);

/// Retrieve pointer to the description of this type.
ROSIDL_GENERATOR_C_PUBLIC_control_msgs
const rosidl_runtime_c__type_description__TypeDescription *
control_msgs__msg__CANopenState__get_type_description(
  const rosidl_message_type_support_t * type_support);

/// Retrieve pointer to the single raw source text that defined this type.
ROSIDL_GENERATOR_C_PUBLIC_control_msgs
const rosidl_runtime_c__type_description__TypeSource *
control_msgs__msg__CANopenState__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support);

/// Retrieve pointer to the recursive raw sources that defined the description of this type.
ROSIDL_GENERATOR_C_PUBLIC_control_msgs
const rosidl_runtime_c__type_description__TypeSource__Sequence *
control_msgs__msg__CANopenState__get_type_description_sources(
  const rosidl_message_type_support_t * type_support);

/// Initialize array of msg/CANopenState messages.
/**
 * It allocates the memory for the number of elements and calls
 * control_msgs__msg__CANopenState__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_control_msgs
bool
control_msgs__msg__CANopenState__Sequence__init(control_msgs__msg__CANopenState__Sequence * array, size_t size);

/// Finalize array of msg/CANopenState messages.
/**
 * It calls
 * control_msgs__msg__CANopenState__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_control_msgs
void
control_msgs__msg__CANopenState__Sequence__fini(control_msgs__msg__CANopenState__Sequence * array);

/// Create array of msg/CANopenState messages.
/**
 * It allocates the memory for the array and calls
 * control_msgs__msg__CANopenState__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_control_msgs
control_msgs__msg__CANopenState__Sequence *
control_msgs__msg__CANopenState__Sequence__create(size_t size);

/// Destroy array of msg/CANopenState messages.
/**
 * It calls
 * control_msgs__msg__CANopenState__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_control_msgs
void
control_msgs__msg__CANopenState__Sequence__destroy(control_msgs__msg__CANopenState__Sequence * array);

/// Check for msg/CANopenState message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_control_msgs
bool
control_msgs__msg__CANopenState__Sequence__are_equal(const control_msgs__msg__CANopenState__Sequence * lhs, const control_msgs__msg__CANopenState__Sequence * rhs);

/// Copy an array of msg/CANopenState messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_control_msgs
bool
control_msgs__msg__CANopenState__Sequence__copy(
  const control_msgs__msg__CANopenState__Sequence * input,
  control_msgs__msg__CANopenState__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // CONTROL_MSGS__MSG__DETAIL__CA_NOPEN_STATE__FUNCTIONS_H_
