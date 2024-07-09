#include "cfr_carr_factor.h"

#include "MathTool_Api.h"
#include "keyword.h"
#include "expection.h"
#include "power_value.h"

#include "dig_if_ch_id.h"
#include "iflogic_define.h"
#include "iflogic_data_rate_def.h"
#include "bsp_cfgpara_tableid.h"
#include "bsp_cfgpara.h"

#include "cfr_define.h"
#include "cfr_ch_api.h"
#include "cfr_do_cpc.h"
#include "cfr_cfg_para.h"
#include "cfr_cfg_para_util.h"
#include "cfr_band_api.h"

MCL_PRIVATE U32 CfrCarrFactor_CalcEvm(CfrCarrFactor *self)
{
    MCL_EXPECT_NON_NIL_R(self, 0);
    MCL_EXPECT_NON_NIL_R(self->dependentPara, 0);

    const CfrCarr *cfrCarr = self->refCfrCarr;
    RxPhyCh *txPhyCh = CfrCarr_GetTxPhyCh(cfrCarr);
    const PhyChId *phyChId = RxPhyCh_GetPhyChId(txPhyCh);
    MCL_EXPECT_NON_NIL_R(phyChId, 0);

    U32 dataRateEnum = CfrCarr_GetDataRateEnum(cfrCarr);

    U32 chMaxBoundaryBw = self->dependentPara->chMaxBoundaryBw;
    S32 maxPwr = self->dependentPara->chMaxPwr_0P01dBm;
    BSP_CARR_BW_MODE_NUM_STRU *allBandCarrSum = &self->dependentPara->bandCarrNum[0];
    U32 bandMap = self->dependentPara->chUsedBandMap;

    U32 fullPwrEvmValue = 0;
    U32 lteFullPwrEvmValue = 0;
    U32 nrFullPwrEvmValue = 0;
    StdType realStandard = CfrCarr_GetRealStandard(cfrCarr);
    MCL_EXPECT_EXEC_R(CfrCfgPara_GetCfrCommEvmPara(phyChId->phyChIdx, dataRateEnum, realStandard, chMaxBoundaryBw, maxPwr,
                                                   allBandCarrSum, EN_BAND_END, bandMap,
                                                   &fullPwrEvmValue, &lteFullPwrEvmValue, &nrFullPwrEvmValue), 0);

    if (self->dependentPara->chIsFullPwrCfgMode) {
        return fullPwrEvmValue;
    }

    S32 chPwrDelta = (S32)self->dependentPara->chPwrDelta;
    BSP_CARR_EXIST_MODE_STRU *carrExistMode = &self->dependentPara->chCarrExistMode;
    CFG_CFR_THRD_COEF_CALC_PARA_STRU cfrThrdCoefPara = { 0 };

    DuplexMode curBrdWorkMode;
    MCL_EXPECT_EXEC(CfrCfgPara_GetTxPhyChDuplexMode(phyChId->phyChIdx, &curBrdWorkMode));
    CfrEvmCfgParaKey evmCfgParaKey;
    evmCfgParaKey.dataRateEnum = dataRateEnum;
    evmCfgParaKey.BrdWorkMode = curBrdWorkMode;
    evmCfgParaKey.pmax_0p01dBm = maxPwr;

    if (self->dependentPara->chCarrExistMode.ucNrExistFlag == 1) {
        evmCfgParaKey.fullPwrEvmValue = nrFullPwrEvmValue;
    } else {
        evmCfgParaKey.fullPwrEvmValue = lteFullPwrEvmValue;
    }
    /* 获取门限抬升量 */
    MCL_EXPECT_EXEC_R(CfrCfgPara_GetEvmOptPara(&evmCfgParaKey, phyChId->phyChIdx, chPwrDelta, 
                                            carrExistMode, &cfrThrdCoefPara), 0);

    return CfrCarrFactor_GetEvmOfCoefPara(&cfrThrdCoefPara, realStandard);
}
