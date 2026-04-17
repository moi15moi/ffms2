from ctypes import (
    CDLL,
    POINTER,
    Structure,
    addressof,
    byref,
    c_char_p,
    c_double,
    c_int,
    c_int64,
    c_uint,
    create_string_buffer,
    sizeof
)
from enum import IntEnum
from pathlib import Path
from platform import system
from urllib.parse import urljoin

import vapoursynth

from download_samples import SAMPLES_FILE, SAMPLES_URL, download


dir_path = Path(__file__).parent


class FFMS_ErrorInfo(Structure):
    _fields_ = [
        ("ErrorType", c_int),
        ("SubType", c_int),
        ("BufferSize", c_int),
        ("Buffer", c_char_p),
    ]


class FFMS_VideoProperties(Structure):
    _fields_ = [
        ("FPSDenominator", c_int),
        ("FPSNumerator", c_int),
        ("RFFDenominator", c_int),
        ("RFFNumerator", c_int),
        ("NumFrames", c_int),
        ("SARNum", c_int),
        ("SARDen", c_int),
        ("CropTop", c_int),
        ("CropBottom", c_int),
        ("CropLeft", c_int),
        ("CropRight", c_int),
        ("TopFieldFirst", c_int),
        ("ColorSpace", c_int),
        ("ColorRange", c_int),
        ("FirstTime", c_double),
        ("LastTime", c_double),
        ("Rotation", c_int),
        ("Stereo3DType", c_int),
        ("Stereo3DFlags", c_int),
        ("LastEndTime", c_double),
        ("HasMasteringDisplayPrimaries", c_int),
        ("MasteringDisplayPrimariesX", c_double * 3),
        ("MasteringDisplayPrimariesY", c_double * 3),
        ("MasteringDisplayWhitePointX", c_double),
        ("MasteringDisplayWhitePointY", c_double),
        ("HasMasteringDisplayLuminance", c_int),
        ("MasteringDisplayMinLuminance", c_double),
        ("MasteringDisplayMaxLuminance", c_double),
        ("HasContentLightLevel", c_int),
        ("ContentLightLevelMax", c_uint),
        ("ContentLightLevelAverage", c_uint),
        ("Flip", c_int),
        ("LastEndPTS", c_int64),
    ]


class FFMS_Indexer(Structure):
    _fields_ = []


class FFMS_Index(Structure):
    _fields_ = []


class FFMS_VideoSource(Structure):
    _fields_ = []


class FFMS_Errors(IntEnum):
    FFMS_ERROR_SUCCESS = 0
    FFMS_ERROR_INDEX = 1
    FFMS_ERROR_INDEXING = 2
    FFMS_ERROR_POSTPROCESSING = 3
    FFMS_ERROR_SCALING = 4
    FFMS_ERROR_DECODING = 5
    FFMS_ERROR_SEEKING = 6
    FFMS_ERROR_PARSER = 7
    FFMS_ERROR_TRACK = 8
    FFMS_ERROR_WAVE_WRITER = 9
    FFMS_ERROR_CANCELLED = 10
    FFMS_ERROR_RESAMPLING = 11

    FFMS_ERROR_UNKNOWN = 20
    FFMS_ERROR_UNSUPPORTED = 21
    FFMS_ERROR_FILE_READ = 22
    FFMS_ERROR_FILE_WRITE = 23
    FFMS_ERROR_NO_FILE = 24
    FFMS_ERROR_VERSION = 25
    FFMS_ERROR_ALLOCATION_FAILED = 26
    FFMS_ERROR_INVALID_ARGUMENT = 27
    FFMS_ERROR_CODEC = 28
    FFMS_ERROR_NOT_AVAILABLE = 29
    FFMS_ERROR_FILE_MISMATCH = 30
    FFMS_ERROR_USER = 31


class FFMS_IndexErrorHandling(IntEnum):
    FFMS_IEH_ABORT = 0
    FFMS_IEH_CLEAR_TRACK = 1
    FFMS_IEH_STOP_TRACK = 2
    FFMS_IEH_IGNORE = 3


class FFMS_SeekMode(IntEnum):
    FFMS_SEEK_LINEAR_NO_RW = -1
    FFMS_SEEK_LINEAR = 0
    FFMS_SEEK_NORMAL = 1
    FFMS_SEEK_UNSAFE = 2
    FFMS_SEEK_AGGRESSIVE = 3


def test_wheel_can_index_video():
    system_name = system()

    if system_name == "Windows":
        library_name = "ffms2.dll"
    elif system_name == "Darwin":
        library_name = "libffms2.dylib"
    else:
        library_name = "libffms2.so"

    vs_dir = Path(vapoursynth.__file__).parent
    dll_path = vs_dir / "plugins" / library_name

    ffms2_dll = CDLL(str(dll_path))

    FFMS_Init = ffms2_dll.FFMS_Init
    FFMS_Init.restype = None
    FFMS_Init.argtypes = [c_int, c_int]

    FFMS_CreateIndexer = ffms2_dll.FFMS_CreateIndexer
    FFMS_CreateIndexer.restype = POINTER(FFMS_Indexer)
    FFMS_CreateIndexer.argtypes = [c_char_p, POINTER(FFMS_ErrorInfo)]

    FFMS_DoIndexing2 = ffms2_dll.FFMS_DoIndexing2
    FFMS_DoIndexing2.restype = POINTER(FFMS_Index)
    FFMS_DoIndexing2.argtypes = [POINTER(FFMS_Indexer), c_int, POINTER(FFMS_ErrorInfo)]

    FFMS_DestroyIndex = ffms2_dll.FFMS_DestroyIndex
    FFMS_DestroyIndex.restype = None
    FFMS_DestroyIndex.argtypes = [POINTER(FFMS_Index)]

    FFMS_CreateVideoSource = ffms2_dll.FFMS_CreateVideoSource
    FFMS_CreateVideoSource.restype = POINTER(FFMS_VideoSource)
    FFMS_CreateVideoSource.argtypes = [
        c_char_p,
        c_int,
        POINTER(FFMS_Index),
        c_int,
        c_int,
        POINTER(FFMS_ErrorInfo),
    ]

    FFMS_DestroyVideoSource = ffms2_dll.FFMS_DestroyVideoSource
    FFMS_DestroyVideoSource.restype = None
    FFMS_DestroyVideoSource.argtypes = [POINTER(FFMS_VideoSource)]

    FFMS_GetVideoProperties = ffms2_dll.FFMS_GetVideoProperties
    FFMS_GetVideoProperties.restype = POINTER(FFMS_VideoProperties)
    FFMS_GetVideoProperties.argtypes = [POINTER(FFMS_VideoSource)]


    # Test the first sample file
    sample_url = urljoin(SAMPLES_URL, SAMPLES_FILE[0])
    sample_dir = dir_path.joinpath("samples")
    if not sample_dir.is_dir():
        sample_dir.mkdir()
    sample_path = sample_dir.joinpath(SAMPLES_FILE[0])
    download(sample_url, sample_path)

    FFMS_Init(0, 0)

    err_msg = create_string_buffer(1024)
    err_info = FFMS_ErrorInfo(
        FFMS_Errors.FFMS_ERROR_SUCCESS,
        FFMS_Errors.FFMS_ERROR_SUCCESS,
        sizeof(err_msg),
        addressof(err_msg),
    )

    indexer = FFMS_CreateIndexer(str(sample_path.absolute()).encode("utf-8"), byref(err_info))
    if not indexer:
        raise Exception("ffms2 reported an error while calling FFMS_CreateIndexer: " + err_info.Buffer.decode("utf-8"))

    index = FFMS_DoIndexing2(indexer, FFMS_IndexErrorHandling.FFMS_IEH_ABORT, byref(err_info))
    if not index:
        raise Exception("ffms2 reported an error while calling FFMS_DoIndexing2: " + err_info.Buffer.decode("utf-8"))

    video_source = FFMS_CreateVideoSource(str(sample_path.absolute()).encode("utf-8"), 0, index, 1, FFMS_SeekMode.FFMS_SEEK_NORMAL, byref(err_info))
    if not video_source:
        raise Exception("ffms2 reported an error while calling FFMS_CreateVideoSource: " + err_info.Buffer.decode("utf-8"))

    video_props = FFMS_GetVideoProperties(video_source)

    assert video_props.contents.FPSNumerator == 30000
    assert video_props.contents.FPSDenominator == 1001

    FFMS_DestroyVideoSource(video_source)
    FFMS_DestroyIndex(index)
