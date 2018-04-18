#version 430 core

in vec2 FragUV;
out vec4 Color;
layout(binding = 0) uniform sampler2D TextureAtlas;

void main() {
    Color = texture(TextureAtlas, FragUV);
    if (Color.a < 0.01) {
        discard;
    }
}