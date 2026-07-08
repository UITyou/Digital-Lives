from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGB', (100, 100), color=(139, 195, 74))
draw = ImageDraw.Draw(img)

font = ImageFont.load_default()

text = input("")
text_bbox = draw.textbbox((0, 0), text)
text_width = text_bbox[2] - text_bbox[0]
text_height = text_bbox[3] - text_bbox[1]
x = (100 - text_width) // 2
y = (100 - text_height) // 2 - 10
draw.text((x, y), text, font=font, fill=(255, 255, 255))

text_name = input("昵称：")
name_bbox = draw.textbbox((0, 0), text_name)
name_width = name_bbox[2] - name_bbox[0]
x = (100 - name_width) // 2
y = 55
draw.text((x, y), text_name, font=font, fill=(255, 255, 255))

img.save('lh.jpg')
print("头像创建成功！")