#version 430 core

layout(location = 0) in vec4 Pos;
layout(location = 1) in vec2 UV;

layout (location = 0) uniform mat4 ModelTransform;
layout (location = 1) uniform mat4 ProjectionView;

out vec2 FragUV;

void main() {
    gl_Position = ProjectionView * ModelTransform * Pos;
    FragUV = UV;
}