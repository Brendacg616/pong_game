#include "ros/ros.h"
#include "pong_game/racket.h"
#include "ros/console.h"

#include <opencv2/videoio.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/aruco.hpp>
#include <opencv2/imgproc.hpp>

int main(int argc, char **argv)
{
    // ROS initialization
    ROS_DEBUG("Initializing ROS");
    ros::init(argc, argv, "visual_controller"); 
    ros::NodeHandle n;
    ros::Publisher gameControlPub = n.advertise<pong_game::racket>("gamecontrol", 10);
    ros::Rate loop_rate(25);
    ROS_DEBUG("Initializing OpenCV");
    // OpenCV aruco detector initialization
    cv::VideoCapture inputVideo;
    inputVideo.open(0);
    // Get camera info width & height
    const int width = static_cast<int>(inputVideo.get(cv::CAP_PROP_FRAME_WIDTH));
    const int height = static_cast<int>(inputVideo.get(cv::CAP_PROP_FRAME_HEIGHT));
    // Create a rectangle sized 80% of camera image size
    cv::Point r1(width*0.1,height*0.1);
    cv::Point r2(width*0.9, height*0.9);
    cv::aruco::DetectorParameters detectorParams = cv::aruco::DetectorParameters();
    cv::aruco::Dictionary dictionary = cv::aruco::getPredefinedDictionary(cv::aruco::DICT_6X6_250);
    cv::aruco::ArucoDetector detector(dictionary, detectorParams);

    while (ros::ok())
    {
        if (inputVideo.grab())
        {
            cv::Mat image;
            inputVideo.retrieve(image);
            std::vector<int> ids;
            std::vector<std::vector<cv::Point2f>> markerCorners;
            detector.detectMarkers(image, markerCorners, ids);
            if (markerCorners.size()>1 )
            {
                ROS_ERROR("More than one marker detected");
            } else if (markerCorners.size() == 1 )
            {
                pong_game::racket racket;
                cv::Point2f center(0.f, 0.f);
                for(const auto& corner : markerCorners.at(0)) {
                    center += corner;
                }
                center /= 4.f;
                if (center.y > height*0.9)
                    racket.position = 1;
                else if (center.y < height*0.1)
                    racket.position = 0;
                else 
                    racket.position = ((center.y-(height*0.1)) / (height*0.8));
                gameControlPub.publish(racket);
                ROS_INFO("Position: %f", racket.position);
                cv::drawMarker(image, center, CV_RGB(255,0,0));
            }
            cv::rectangle(image, r1, r2, CV_RGB(0,0,255),5);
            // Mirror camera image for feedback to feel more natural
            flip(image, image, 1);
            cv::imshow("camera feedback", image);  
            cv::waitKey(10);
        }
        loop_rate.sleep();
    }
}