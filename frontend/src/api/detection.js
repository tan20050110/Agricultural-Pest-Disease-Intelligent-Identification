import request from '../utils/request'

/**
 * 发送单帧图像到后端进行摄像头实时检测
 * @param {Object} data - { image: "base64编码的图像数据" }
 * @returns {Promise}
 */
export const detectFrame = (data) => {
  return request({
    url: '/camera/detect',
    method: 'post',
    data,
    timeout: 10000
  })
}

/**
 * 启动摄像头检测服务
 * @param {Object} data - { confidence_threshold, iou_threshold, inference_interval }
 * @returns {Promise}
 */
export const startDetection = (data) => {
  return request({
    url: '/camera/start',
    method: 'post',
    data
  })
}

/**
 * 停止摄像头检测服务
 * @returns {Promise}
 */
export const stopDetection = () => {
  return request({
    url: '/camera/stop',
    method: 'post'
  })
}

/**
 * 暂停摄像头检测
 * @returns {Promise}
 */
export const pauseDetection = () => {
  return request({
    url: '/camera/pause',
    method: 'post'
  })
}

/**
 * 恢复摄像头检测
 * @returns {Promise}
 */
export const resumeDetection = () => {
  return request({
    url: '/camera/resume',
    method: 'post'
  })
}

/**
 * 获取检测状态
 * @returns {Promise}
 */
export const getDetectionStatus = () => {
  return request({
    url: '/camera/status',
    method: 'get'
  })
}
