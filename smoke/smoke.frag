#version 450
// A fragment stage with a uniform block, a texture and a cubemap: what the smoke test compiles and translates on every platform.
layout(location = 0) in vec2 v_uv;
layout(binding = 2) uniform params { vec4 tint; mat4 turn; };
layout(binding = 0) uniform sampler2D image;
layout(binding = 1) uniform samplerCube sky;
layout(location = 0) out vec4 color;
void main() { color = texture(image, v_uv) * tint + texture(sky, (turn * vec4(v_uv, 1.0, 0.0)).xyz); }
