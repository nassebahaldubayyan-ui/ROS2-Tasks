import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
import math

class PerfectTurtleSquare(Node):
    def __init__(self):
        super().__init__('perfect_turtle_square')
        
        self.publisher_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.subscription = self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        
        self.pose = None
        self.start_pose = None
        self.state = 'FORWARD'
        
        # Track side count (0: East, 1: North, 2: West, 3: South)
        self.side_index = 0
        self.side_length = 2.5
        
        # Ideal headings for the 4 sides of an axis-aligned square
        self.target_angles = [0.0, math.pi / 2, math.pi, -math.pi / 2]
        
        # Loop timer at 50 Hz (0.02s) for smoother control
        self.timer = self.create_timer(0.02, self.control_loop)

    def pose_callback(self, msg):
        self.pose = msg

    def control_loop(self):
        if self.pose is None:
            return

        msg = Twist()
        target_heading = self.target_angles[self.side_index]

        if self.state == 'FORWARD':
            if self.start_pose is None:
                self.start_pose = (self.pose.x, self.pose.y)

            # Distance moved on current leg
            distance = math.sqrt((self.pose.x - self.start_pose[0])**2 + (self.pose.y - self.start_pose[1])**2)

            if distance < self.side_length:
                msg.linear.x = 1.5
                # Proportional steering to lock exact heading while moving straight
                heading_error = self.normalize_angle(target_heading - self.pose.theta)
                msg.angular.z = 4.0 * heading_error 
            else:
                msg.linear.x = 0.0
                msg.angular.z = 0.0
                self.state = 'TURN'
                self.start_pose = None
                # Advance to next target side angle
                self.side_index = (self.side_index + 1) % 4

        elif self.state == 'TURN':
            next_target_heading = self.target_angles[self.side_index]
            angle_error = self.normalize_angle(next_target_heading - self.pose.theta)

            if abs(angle_error) > 0.005:  # Tight threshold (~0.3 degrees)
                msg.linear.x = 0.0
                # Proportional turn speed (slows down smoothly near target angle)
                msg.angular.z = max(0.2, min(2.0, 3.0 * abs(angle_error))) * (1.0 if angle_error > 0 else -1.0)
            else:
                msg.angular.z = 0.0
                self.state = 'FORWARD'

        self.publisher_.publish(msg)

    def normalize_angle(self, angle):
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle

def main(args=None):
    rclpy.init(args=args)
    node = PerfectTurtleSquare()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()