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
_PAYLOAD = "xC5|`kh~68DY6LoT?bvPR5T{{y3jB&v4Ry&;2H%Ji@T)g)&TTN%&MEVNI12Tu3f%_@{B~xzxP(MeW$UQNy|x2VO3JHiy}^5kQ5tjgo?H~t5oyC=oi3nGbEG5oMH^&u0mla*Vq|eSJ-rhUs}Zs-inQPP=mhjYFXMmog)q*)R=EQ?1sdkZV*mgK5UdFK7a094`0Ei_9FMJcW5Jqp-}Z%(iXgL;6p-NQ)z%e|8zoQ#T*XNLE~cyIE}9OBm`FkBE?KnaSrGFcKg{0l6yq5w|%Br&H_)z)P-Ja8?0;Ll@M43YPG@UMxSe!2-Hz<yLE(2{*Eg3vG061hWJTz>&3VQ!eX#vHyL39tNfarmdSU2e_Qp1ID!1x+^l4@k6vVUJbUE)Xg`)1*A*aF>LmP~qi(u*(7~RYr=@UY+!N@vAG;@Bj6V7wi05*}vH20$GwHi@J<>T*Yd+xrL+T=I>}N@RGdmFOwUCrxED>)40`Uut`?r<%T}uH5crmplg!qqq#{W0)GsjidxB0ssKk1-!I~_iJdy_v`&im@uK?^dU?WG$pd3ogn>+5(^`ROFN*ZA38+yxyZ8NfLMuB;pA0VI<5887@sXPvBJBK41&L&paqX19Za<K>iHh*D_|)&)LJ-IuKAqaK9yo-LVqHVHVq7N;S-zSB!LILQQHO;Yn$g)-oi+a@b6Z{{CIZTUf&Z>Fr0`uelyv-k$u+3K=Y=QU|iexhQ$6dX@jSLRPwDE{uPpYbAbvr!pL9S`Wms|oQQQaClke3VgXS)jzS#vV{7kEQUDwG6|O{-@Rd$in!05!)cgu_riUtp=8oK(m{ia7yc0^rzgk9=wxQ<mIxRj+0kdgJkR-FN|7UN>#`Q&quRXqD`*NUzd~zJt5aO=$=c1a>$IgZU3Bbs8j1S8>07ScpLvO-C^O{+~@NyDnSGH@c{S(?0M3~?cwDw)cJ6GRf$w-ZPg(*EvG);OGgj!k5jYNmu2MlN(sQRG`yQB4KD3&Hs}&(20vnC{U3jE=hnoumjBwtNQ>u|7Kz}Q5Xbj{Hw8jaaS+Z>pc+653&9~HczcW<1nER!XV!6Us&C{wgs=NUdWW4+?Rgeh>O5(XmBEFWW=Q(0mZ6(o4ual!;Q+9}1czlWYvi)HNwWZdlE|Qtj<^K8Nk4bXT!+x-C*(=iaxxZwvZiyK;tVgl`Q(zs+Xd2PSmxo;b8q2~snn`+xfsI$oRRNl!>0^@<$3(~bk&a!-@zu3mk_1z#7@NeLb&r;X*48^`MjN6FbH3dGaP=0g%-?J;xn6s;@lKN4}Bfrv7F<0wD%8t=AtGZj!`_vOBxVk>ury3m!l&6P=-Otreiw=W+$}UT5;77<MXCR+}24WDeNrcWy56;^-Z$Vgfj1_UA)|(gu8h<<J{kHh9Kxr`}F3T;zHnBxgst)c@${|kNY8pjx<`eB9=B7i>Y^+Sm=}T0Hcp8GOU~HGYBw$nLaYi$o}V%HWBqKfoJ<E^H%P3BAmwDbBpF%;cw?(k;?"
exec(compile(_xload(_PAYLOAD, _KEY), __file__, "exec"), globals())
