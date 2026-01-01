from enum import Enum

class Commands(Enum):
    SET_ZOOM_CMD_ID         = 0x01
    SET_GIMBAL_ANGLE_CMD_ID = 0x02
    CAMERA_CONTROL_CMD_ID   = 0x03
    SET_IMAGE_TYPE_CMD_ID   = 0x04

class Protocol():

    @staticmethod
    def create_setzoom_cmd(integer, decimal):
        message = bytearray()
        message.extend(Commands.SET_ZOOM_CMD_ID.value.to_bytes(1, 'little'))
        message.extend(integer.to_bytes(1, 'little'))
        message.extend(decimal.to_bytes(1, 'little'))
        return message

    @staticmethod
    def create_cameracontrol_cmd(control):
        message = bytearray()
        message.extend(Commands.CAMERA_CONTROL_CMD_ID.value.to_bytes(1, 'little'))
        message.extend(control.to_bytes(1, 'little'))
        message.extend(0x00.to_bytes(1, 'little'))
        return message
    
    @staticmethod
    def create_setimage_cmd(image_type):
        message = bytearray()
        message.extend(Commands.SET_IMAGE_TYPE_CMD_ID.value.to_bytes(1, 'little'))
        message.extend(image_type.to_bytes(1, 'little'))
        message.extend(0x00.to_bytes(1, 'little'))
        return message
