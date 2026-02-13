#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from kelo_tulip.msg import KeloDrivesInput
from rclpy.qos import qos_profile_sensor_data  # BEST_EFFORT, depth=10, VOLATILE

VALID_ORDERS = {"LRP", "LPR", "RLP", "RPL", "PLR", "PRL"}

class WheelsToJointStates(Node):
    """
    /platform_driver/wheels_input (KeloDrivesInput) --> /joint_states (JointState)

    For each wheel i, map:
      encoder_1     -> {wheel}_mid_left_hub_wheel_joint
      encoder_2     -> {wheel}_mid_right_hub_wheel_joint
      encoder_pivot -> {wheel}_mid_pivot_joint

    The ordering of the triplet in the JointState can be controlled with 'triplet_order'
    so names and positions always match (default 'LRP').
    """

    def __init__(self) -> None:
        super().__init__('wheels_to_joint_states')

        # Parameters
        self.declare_parameter('wheel_names', ['wheel0', 'wheel1', 'wheel2', 'wheel3'])
        self.declare_parameter('encoders_in_degrees', False)
        self.declare_parameter('triplet_order', 'LRP')  # choose from VALID_ORDERS

        self.wheel_names = list(
            self.get_parameter('wheel_names').get_parameter_value().string_array_value
        )
        self.enc_deg = bool(
            self.get_parameter('encoders_in_degrees').get_parameter_value().bool_value
        )
        self.triplet_order = str(
            self.get_parameter('triplet_order').get_parameter_value().string_value
        ).upper()
        if self.triplet_order not in VALID_ORDERS:
            self.get_logger().warn(
                f"Invalid triplet_order '{self.triplet_order}', falling back to 'LRP'."
            )
            self.triplet_order = 'LRP'

        # Sub/Pub (BEST_EFFORT to match robot_state_publisher)
        self.sub = self.create_subscription(
            KeloDrivesInput, '/platform_driver/wheels_input', self._cb, 10
        )
        self.pub = self.create_publisher(JointState, '/joint_states', qos_profile_sensor_data)

        self.get_logger().info(
            f"wheel_names={self.wheel_names}, encoders_in_degrees={self.enc_deg}, "
            f"triplet_order={self.triplet_order}"
        )

    def _cb(self, msg: KeloDrivesInput) -> None:
        wheels = msg.wheels
        if not wheels:
            return

        out = JointState()
        out.header.stamp = self.get_clock().now().to_msg()  # non-zero timestamp

        to_rad = 0.017453292519943295 if self.enc_deg else 1.0

        names: list[str] = []
        positions: list[float] = []

        # Build names+positions per wheel according to triplet_order
        for i, wname in enumerate(self.wheel_names):
            if i >= len(wheels):
                self.get_logger().warn(
                    f'Missing wheel index {i} in message (have {len(wheels)}); filling zeros.'
                )
                e1 = e2 = ep = 0.0
            else:
                w = wheels[i]
                e1 = float(w.encoder_1) * to_rad  # L
                e2 = float(w.encoder_2) * to_rad  # R
                ep = float(w.encoder_pivot) * to_rad  # P

            # Triplet name map
            name_map = {
                'L': f'{wname}_mid_left_hub_wheel_joint',
                'R': f'{wname}_mid_right_hub_wheel_joint',
                'P': f'{wname}_mid_pivot_joint',
            }
            # Triplet value map
            val_map = {'L': e1, 'R': e2, 'P': ep}

            for key in self.triplet_order:
                names.append(name_map[key])
                positions.append(val_map[key])

        out.name = names
        out.position = positions
        self.pub.publish(out)


def main() -> None:
    rclpy.init()
    rclpy.spin(WheelsToJointStates())
    rclpy.shutdown()


if __name__ == '__main__':
    main()
