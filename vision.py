import cv2
import numpy as np
import apriltag
import fiducial_detector
import imutils


tag_world_positions = {
    'tag36h11_0': np.array([0, 0]),
    'tag36h11_1': np.array([500, 0]),
    'tag36h11_2': np.array([500, 350]),
    'tag36h11_3': np.array([0, 350]),
}
lower = (0, 100, 100)
upper = (80, 255, 255)
min_detection_area = 300


if __name__ == '__main__':
    detector = fiducial_detector.ApriltagDetector(tag_families="tag36h11")
    img = imutils.resize(cv2.imread('img/IMG_0222.png'), width=1200)

    # Find apriltag locations
    tags = detector.detect_tags(img)
    camera_locations = []
    world_locations = []
    for tag in tags:
        tag_name = f"{tag.tag_family.decode('utf-8')}_{tag.tag_id}"
        if tag_name in tag_world_positions:
            camera_locations.append(tag.center)
            world_locations.append(tag_world_positions[tag_name])
    print(f"Tags found: {len(tags)}")
    # Compute cv2 homography matrix
    homography_matrix, status = cv2.findHomography(np.array(camera_locations),
                                                   np.array(world_locations))
    print(homography_matrix)

    # Find sticky notes
    blurred = cv2.GaussianBlur(img, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    cv2.imshow("mask",mask)
    contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)

    objs = []
    for c in contours:
        if cv2.contourArea(c) < min_detection_area:
            continue
        moments = cv2.moments(c)
        x, y, w, h = cv2.boundingRect(c)
        center = (int(moments["m10"] / moments["m00"]),
                  int(moments["m01"] / moments["m00"]))
        center_world = np.dot(homography_matrix,
                              np.array([center[0], center[1], 1]))
        objs.append(([x, y, w, h], center, center_world))


    # Annotate frame
    detector.annotate_frame(img,tags)
    for obj in objs:
        pos, center, center_world = obj
        cv2.circle(img, center, 5, (255, 0, 0), -1)
        cv2.rectangle(img, (pos[0], pos[1]), (pos[0]+pos[2], pos[1]+pos[3]),
                      (0, 255, 0), 2)
        cv2.putText(img, str(center_world[0:2]), (center[0], center[1] - 15),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    cv2.imshow("Annotated img", img)
    cv2.waitKey(0)
