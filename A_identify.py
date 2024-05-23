import colorsys
import os
import time
import cv2
import numpy as np
import torch
import torch.backends.cudnn as cudnn
from PIL import ImageDraw, ImageFont, Image

from nets.centernet import CenterNet_HourglassNet, CenterNet_Resnet50
from utils.utils import (cvtColor, get_classes, preprocess_input, resize_image,
                         show_config)
from utils.utils_bbox import decode_bbox, postprocess


class Identify:
    def __init__(self):
        self.cap = cv2.VideoCapture()
        # 参数定义
        self.model_path = 'logs/5_6_50_epoch_hourglass_best_epoch_weights.pth'
        self.classes_path = 'model_data/voc_classes.txt'
        self.backbone = 'hourglass'  # 用于选择所使用的模型的主干
        self.input_shape = [512, 512]  # 输入图片的大小，必须为32的倍数
        self.confidence = 0.15  # 置信度，只有得分大于置信度的预测框会被保留下来
        self.nms_iou = 0.3  # 非极大抑制所用到的nms_iou大小
        self.nms = False  # 是否进行非极大抑制，可以根据检测效果自行选择
        self.letterbox_image = False   # 该变量用于控制是否使用letterbox_image对输入图像进行不失真的resize
        self.cuda = True  # 是否使用Cuda,没有GPU可以设置成False
           #---------------------------------------------------#
        #   计算总的类的数量
        #---------------------------------------------------#
        self.class_names, self.num_classes  = get_classes(self.classes_path)
        #---------------------------------------------------#
        #   画框设置不同的颜色
        #---------------------------------------------------#
        hsv_tuples = [(x / self.num_classes, 1., 1.) for x in range(self.num_classes)]
        self.colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
        self.colors = list(map(lambda x: (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)), self.colors))
        #-------------------------------#
        #   载入模型与权值
        #-------------------------------#
        assert self.backbone in ['resnet50', 'hourglass']
        if self.backbone == "resnet50":
            self.net = CenterNet_Resnet50(num_classes=self.num_classes, pretrained=False)
        else:
            self.net = CenterNet_HourglassNet({'hm': self.num_classes, 'wh': 2, 'reg':2})

        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.net.load_state_dict(torch.load(self.model_path, map_location=device))
        self.net    = self.net.eval()
        print('{} model, and classes loaded.'.format(self.model_path))
        if self.cuda:
            self.net = torch.nn.DataParallel(self.net)
            self.net = self.net.cuda()

    def show_frame(self, img, cap_flag):
        if cap_flag:
            flag, img = self.cap.read()
        if img is not None:
            image = img.copy()
            labels = []
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            image_shape = np.array(np.shape(image)[0:2])
            image = cvtColor(image)
            image_data = resize_image(image, (self.input_shape[1], self.input_shape[0]), self.letterbox_image)
            image_data = np.expand_dims(np.transpose(preprocess_input(np.array(image_data, dtype='float32')), (2, 0, 1)), 0)
            with torch.no_grad():
                images = torch.from_numpy(np.asarray(image_data)).type(torch.FloatTensor)
                if self.cuda:
                    images = images.cuda()
                #---------------------------------------------------------#
                #   将图像输入网络当中进行预测！
                #---------------------------------------------------------#
                outputs = self.net(images)
                if self.backbone == 'hourglass':
                    outputs = [outputs[-1]["hm"].sigmoid(), outputs[-1]["wh"], outputs[-1]["reg"]]
                #-----------------------------------------------------------#
                #   利用预测结果进行解码
                #-----------------------------------------------------------#
                outputs = decode_bbox(outputs[0], outputs[1], outputs[2], self.confidence, self.cuda)

                #-------------------------------------------------------#
                #   对于centernet网络来讲，确立中心非常重要。
                #   对于大目标而言，会存在许多的局部信息。
                #   此时对于同一个大目标，中心点比较难以确定。
                #   使用最大池化的非极大抑制方法无法去除局部框
                #   所以我还是写了另外一段对框进行非极大抑制的代码
                #   实际测试中，hourglass为主干网络时有无额外的nms相差不大，resnet相差较大。
                #-------------------------------------------------------#
                results = postprocess(outputs, self.nms, image_shape, self.input_shape, self.letterbox_image, self.nms_iou)
                
                #--------------------------------------#
                #   如果没有检测到物体，则返回原图
                #--------------------------------------#
                if results[0] is None:
                    return img, img, []

                top_label   = np.array(results[0][:, 5], dtype = 'int32')
                top_conf    = results[0][:, 4]
                top_boxes   = results[0][:, :4]
                
            #---------------------------------------------------------#
            #   设置字体与边框厚度
            #---------------------------------------------------------#
            # font = ImageFont.truetype(font='model_data/simhei.ttf', size=np.floor(3e-2 * np.shape(image)[1] + 0.5).astype('int32'))
            font = ImageFont.truetype(font='model_data/simhei.ttf', size=np.floor(3e-2 * np.shape(image)[1]).astype('int32'))
            thickness = max((np.shape(image)[0] + np.shape(image)[1]) // self.input_shape[0], 1)
            for i, c in list(enumerate(top_label)):
                predicted_class = self.class_names[int(c)]
                labels.append(predicted_class)  # 添加进标签列表
                box = top_boxes[i]
                score = top_conf[i]
                top, left, bottom, right = box
                top = max(0, np.floor(top).astype('int32'))
                left = max(0, np.floor(left).astype('int32'))
                bottom = min(image.size[1], np.floor(bottom).astype('int32'))
                right = min(image.size[0], np.floor(right).astype('int32'))

                label = '{} {:.2f}'.format(predicted_class, score)
                draw = ImageDraw.Draw(image)
                label_size = draw.textsize(label, font)
                label = label.encode('utf-8')   
                if top - label_size[1] >= 0:
                    text_origin = np.array([left, top - label_size[1]])
                else:
                    text_origin = np.array([left, top + 1])

                for i in range(thickness):
                    #draw.rectangle([left + i, top + i, right - i, bottom - i], outline=self.colors[c])
                    draw.rectangle([left + i, top + i, right - i, bottom - i], outline=self.colors[c])
                #draw.rectangle([tuple(text_origin), tuple(text_origin + label_size)], fill=self.colors[c])

                #draw.text(text_origin, str(label,'UTF-8'), fill=(0, 0, 0), font=font)
                del draw
            # 将 PIL 图像转换为 NumPy 数组
            numpy_image = np.array(image)
            # 将图像从 RGB 格式转换为 BGR 格式
            opencv_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
            return img, opencv_image, labels
        else:
            return None, None, []
        

if __name__ == "__main__":
    idp = Identify()
    img = cv2.imread("img/test1.jpg")
    img1, img2, labels = idp.show_frame(img, False)
    print(labels)
    cv2.imshow("1", img2)
    cv2.waitKey(0)

