from enum import Enum

class Commands(Enum):
    SET_ZOOM_CMD_ID         = 0x01
    SET_GIMBAL_ANGLE_CMD_ID = 0x02
    CAMERA_CONTROL_CMD_ID   = 0x03
    SET_IMAGE_TYPE_CMD_ID   = 0x04
    SELECT_AREA_CMD_ID      = 0x05

class Protocol():

    @staticmethod
    def create_set_zoom_cmd(integer, decimal):
        message = bytearray()
        message.extend(Commands.SET_ZOOM_CMD_ID.value.to_bytes(1, 'little'))
        message.extend(integer.to_bytes(1, 'little'))
        message.extend(decimal.to_bytes(1, 'little'))
        message.extend(0x00.to_bytes(1, 'little'))
        message.extend(0x00.to_bytes(1, 'little'))
        return message

    @staticmethod
    def create_set_angles_cmd(pan, tilt, reset):
        message = bytearray()
        message.extend(Commands.SET_GIMBAL_ANGLE_CMD_ID.value.to_bytes(1, 'little'))
        message.extend(pan.to_bytes(1, 'little'))
        message.extend(tilt.to_bytes(1, 'little'))
        message.extend(reset.to_bytes(1, 'little'))
        message.extend(0x00.to_bytes(1, 'little'))
        return message

    @staticmethod
    def create_camera_control_cmd(control):
        message = bytearray()
        message.extend(Commands.CAMERA_CONTROL_CMD_ID.value.to_bytes(1, 'little'))
        message.extend(control.to_bytes(1, 'little'))
        message.extend(0x00.to_bytes(1, 'little'))
        message.extend(0x00.to_bytes(1, 'little'))
        message.extend(0x00.to_bytes(1, 'little'))
        return message
    
    @staticmethod
    def create_set_image_type_cmd(image_type):
        message = bytearray()
        message.extend(Commands.SET_IMAGE_TYPE_CMD_ID.value.to_bytes(1, 'little'))
        message.extend(image_type.to_bytes(1, 'little'))
        message.extend(0x00.to_bytes(1, 'little'))
        message.extend(0x00.to_bytes(1, 'little'))
        message.extend(0x00.to_bytes(1, 'little'))
        return message

    @staticmethod
    def create_select_area_cmd(x, y, w, h):
        message = bytearray()
        message.extend(Commands.SELECT_AREA_CMD_ID.value.to_bytes(1, 'little'))
        message.extend(x.to_bytes(1, 'little'))
        message.extend(y.to_bytes(1, 'little'))
        message.extend(w.to_bytes(1, 'little'))
        message.extend(h.to_bytes(1, 'little'))
        return message
