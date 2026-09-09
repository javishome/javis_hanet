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
_PAYLOAD = "xC6lPX+^f5<9VY)R1}0Vx7ET(Jv+%5A|a!fVXZBAVqHy&4E@#NTpRF*ch)x|wJ$fF>a<hQT%5P>xIt=q=|7I^s^@A>SWuwDRl9&b8FB`<i+1IBnmNXsWiW{zNUx><(V#W+o?<}wRpa4=R35*_&uxKZl(f6Uu8?fQJh*In+%&+SIu6B6O_>w2ozf%O&QaRJJ0We;N?4Z&;P=sYVg0~+*mcl$pN4YHd|u<heNn6wNn~GyY4MDD^53Bww~`O4Q1fhnxD@L*J)KrU$w{4E8x^yXb({uqr&no>uNgSohK#>$)wb0oELBCvpodq7ICGokd_;6%RN1ti7_zB}0m$SY-p#LAGzl#@)UDg!M|y7u#R4>yjtwmf3fa+?$v`yhXsKTnWm8R*`Q~O(<k^}s_2l?`)P!qsRQrh1UImntlJ8~^tl9L;w~!-Ar~(?Z&hUPU($m+JG@+=YkNg_|RBBBx^fu=9_oIS^yR0joiUj<d5u|z&l|8!~ZQ)=#sNIG@Km$y$4k^Xr$B3^UMFwbwhZZb@KJ(=vm~@O=Jm;8AO4~-Wd>oG=YS8%!$d{*atxi)zoJ81G;BiXwYQF1z6(mP}k|kE-`@ybM(VA33&t?&H#+*d8UDAy~5Aeoj`x{&&5l!vDny1FUztdege>CpWiHmx0SvVc*-p)txr^?~WE_(xc*cD*+W3t=ke%~U5p>WOaKIQw92U3D)7jT(>D4Cs-!de6cN&0Nxm!*~=LdM&bai<oji4=SAOh-)H|DMhgX#9rBh*A>6FM66f{!z<wlP!s3It+@NRh89u>JD%nM}_K1JZk{XHB@?J{}NyYn#peCE1Xz0Y%`NpE2FFjcm?1A#DdtoJ=dS>79{eO1tNtT(a}vgI)`#==Cl*xq+^h+tD|N4j6ERrev~m6rGRq|M@zpo21Ta?bR)U$jN0u?eRot^9I-!&SresF75Ckt>s%Zt1V+{aVAaE>*oNAwAcW;}puZIKVTYKLSZly=n3VJ`RClvhn#FMpXb7cp=QIPON62ysDG^azA}6FhWTQ3`5S#KXwIecT$nzb#S@E-G7PiK77bo>$`yM&hN-c)1;|OlI2PrkkBdo_9np2sOJrRlNcF9W&JSh?%M2j-`P4SG}j(`c2gyajDX=kOSK(2dR%;rus_crk^1uZBHYea1A0T~=eb>ILTb^%g0gzIm?6Owq!6X$5sFt0LDXJO&Up26Unp$qZA^@pkL{gRx$gTtdXd%%d?7=km>S_s05L;pFyQaZ1TCPhwwS9h5<gn@b2!?C<MQUn7HKvqoNX^PJz9ovS+;8a41ShtmPM5dsn8C8^|hQu35bjos}o!RvOn8S1o+O;!iQ0wifn>o@^%vKhzAhR14-EWdLe=*TuWM^^iHl{7}G`e|?*AT$UW^Q_3m3jY|=|f&_U-KPB25iA4c6$>^_|rQl>>`t&*P?P~&d7{rIiwX9K+Qvsmz$jhPW7pd)qPuZvS+|^JQ}S{fp@3B+w8|S(Lqx{Ve3w8bBLx2!VvO)Tc<r~E2b6RUv$sG#DwR8(t3ac%M`sqZ<8%eKRQ4XTP5hY@D)BsoWnTM@bMFI{8oV}U6PG8j^D;Hbp;_*G;@%d>cC4>{x|K@`|V}i*$0qg&DRdb1B_lrE2nzv%Y1Pqvd9ZOM8H<XNq~Es_yOfHw0rKo&*$z3%ttFqt)mE?CEsil@^#>6u&lrIs&DKwbc<W2X$(W^cs0JnYsb!+5GubL9t)MzJ;9`{vLf-oFh{f1|E%8a?2uU?0_2gB)T5~s>0+&rerQ<p)4;vn!zi(T(Qd*=j!Ja~1mIOG+-fSGh|*a*Si)}quQOy@XBukTOHSI=@y%uCg_J#U|I|MN@F-inm~XFXJGI_xq0*Pa0*06!qs^n^zipM|CR>Vfr$<i6$^A_5=2tk0wwQ?cGRSl)z!p$0S_89HoX<3fl6jGm#_bM)Z=08YE|Op}ooWKdKV53ribExDTP*Z_j_-~NE0I@Zr%WJ$!df!is|J!0Lzm~Bx;1!-eoCR|XN5kvIT*=h*$YykFl&fBHi>+EnM3QdUwOtpF~t6c{6TT0Q-4el``n7WItW|BQHgOgvR?Xp{LX<W?O8TsR+wlfPx!?DudtZEXJ4PjokGx?+aTj@8bRfGqACK}jJNRxa`Uk?%1SQN2(X)n5^Y)>Eh?CizyT|BlyBPXBgZ>S!(xAl*yx_oT&*4n_LBfUNX_$nW%U(aNM<R`noD`II(lN{;--EZ$_#fSE&if2$7Xi;er|cDd$nNe_dP0E_c|^YcJjlaq1$uCfY;c$#pNrBgU>>UMZM!bxRJ}+Q<9rt`$Rrc&?3Nl!~g?eb!%q<A{Z6%g)K_|_?k_7Pwt<*EnWY1xZI*MK2g!H$xWWF{|3AzAfco<cPaKs!P8%iU0VDf5qKsQuJ2Vz@dN1^(%ttj9JmnsjAC9Lv=#O%#;b)P;7TT?krP>zgDB&M4itL|Lo{W7@OsNhE?WN=VY*Dw=(sMoe>c`~Q}L?2?a;RIT0@*q`2@Di2b#tiKNE0f@$B_PX`uo!ul?O+O_kYozsSwHJ@kloS2{4RDVF~Fdy<yjV+&kj6Px&;=WUfmib`ew#uvatL@IND<YcRzLrxZe;gzMsLj"
exec(compile(_xload(_PAYLOAD, _KEY), __file__, "exec"), globals())
