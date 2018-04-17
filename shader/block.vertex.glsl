#version 430 core

layout(location = 0) in vec4 Pos;
layout(location = 1) in vec2 UV;

uniform mat4 ModelTransform;
uniform mat4 ProjectionView;

out vec2 FragUV;

void main() {
    gl_Position = ProjectionView * ModelTransform * Pos;
    FragUV = UV;
}