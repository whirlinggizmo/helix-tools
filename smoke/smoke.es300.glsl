#version 300 es
precision mediump float;
precision highp int;

layout(std140) uniform params
{
    highp vec4 tint;
    highp mat4 turn;
} _23;

uniform highp sampler2D image;
uniform highp samplerCube sky;

layout(location = 0) out highp vec4 color;
in highp vec2 v_uv;

void main()
{
    color = (texture(image, v_uv) * _23.tint) + texture(sky, (_23.turn * vec4(v_uv, 1.0, 0.0)).xyz);
}

