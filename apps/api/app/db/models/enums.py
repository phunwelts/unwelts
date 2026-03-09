import enum


class MoodType(str, enum.Enum):
    happy = "happy"
    sad = "sad"
    anxious = "anxious"
    angry = "angry"
    excited = "excited"
    calm = "calm"
    tired = "tired"
