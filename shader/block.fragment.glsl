#version 430 core

in vec2 UV;
out vec4 Color;
layout(binding = 0) uniform sampler2D TextureAtlas;

void main() {
    UV = texture(TextureAtlas, UV);
}