cbuffer params : register(b2, space0)
{
    float4 _23_tint : packoffset(c0);
    row_major float4x4 _23_turn : packoffset(c1);
};

Texture2D<float4> image : register(t0, space0);
SamplerState _image_sampler : register(s0, space0);
TextureCube<float4> sky : register(t1, space0);
SamplerState _sky_sampler : register(s1, space0);

static float4 color;
static float2 v_uv;

struct SPIRV_Cross_Input
{
    float2 v_uv : TEXCOORD0;
};

struct SPIRV_Cross_Output
{
    float4 color : SV_Target0;
};

void frag_main()
{
    color = (image.Sample(_image_sampler, v_uv) * _23_tint) + sky.Sample(_sky_sampler, mul(float4(v_uv, 1.0f, 0.0f), _23_turn).xyz);
}

SPIRV_Cross_Output main(SPIRV_Cross_Input stage_input)
{
    v_uv = stage_input.v_uv;
    frag_main();
    SPIRV_Cross_Output stage_output;
    stage_output.color = color;
    return stage_output;
}
