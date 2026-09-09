# -*- coding: utf-8 -*-
# Protected by Javis Universal Dynamic Encrypted Loader
import base64 as _b85, zlib as _zl
def _xload(_s, _k):
    _e = _b85.b85decode(_s)
    _o = bytearray()
    _p = 0xAA
    _kl = len(_k)
    for _i, _b in enumerate(_e):
        _o.append(_b ^ (_k[_i % _kl] ^ _p))
        _p = _b
    return _zl.decompress(bytes(_o))

_KEY = b'javis_hanet_universal_dynamic_loader_2026_'
_PAYLOAD = "xC7WF2RHrPrbg{WXPF)7?Xv5-K8?wv+WobOT7`sBS*t_m{)w4FHiH+9W=?#MiZ~mHc_tu$-fQbc%@hQ=-!;UNM}FmeEp6Xd3!f%yiCzaLix-8iGeuO>%W|B39JUyX%*W_^qS43;k2uknQa-zn*lWeURB$TLB)EJSN{5ts#6?SG>4byP2Mo(OYK}rqbDX?O1G*UQj>|#U8#Hbaob2jz58qV%yy#UH_E0<y%y<hEC(-qU%ZY0Pzc@w4Uv_Eiev%e;mQ-#;fI5L2UP#|KhUk<%mAh||yn8Ud2UNIyyH?)dM<DRf;^<`y7X4vV;-~tdymR0h2^=Vf!OzZA>ZYk`rL>v&-o%}GZma<x{<?MMB|8o8C`@>!>bxV!!kycHY_~kkKL#!bOJe{h>AClAe>SknV>s9*p#sGfbg&45Hxh0s^$jirXY-+Z{%XFss`Hq**=tWm^cEj_;&sxYoa=X>bU<(saa+=J_-wSOJc|yNIf`#{an|iUhw!)Vzc^1=LARS0g&RpHbe)|2?aDc{Luq9AT}^M+o(5m?#in~TiK}^yQihrfU0CyNsI7BXB6ha4<4%$pa>$4TZ<ER5E@r{1c8Nq;C^RhhNUiKga2n1TAJSA?L!NVQF0Z)vt^?)qH(vPz?!`QK-O`A?L=u`%GX*WN>R7VdZEB|;9vKinqTs58GhW*)^@q+yAENFdXZ5me`Wo!01a*En9eHiQG5VH&L={sHN`#ua!nIlh)*|@+O+VOUS3qV%EZ`jQS*v3H2c3Z;I5SYxr8X=hbQNQvc3j+9x$eCtkW^>YM)dO>LR_EV>7=Y2+Zxw*SB_Q<v%2R7#Ot+iB+@?#*1{L8&+{2+AZxA&_haMZKg$=DeoWR?R$qr=;|+-g+a{+is)718W+hSu<HoSQvB?8^9Zf7$x$Rkpd_#?9NFKZLSzKx0MWD3E?j42hEsc|{ybIsp*bv6(3GjNHCs<5h|NYR)OK}?aO^N"
exec(compile(_xload(_PAYLOAD, _KEY), __file__, "exec"), globals())
